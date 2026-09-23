def _cott_import_module_name(path):
    if path.startswith("/") or "\\" in path:
        return None
    parent, _, filename = path.rpartition("/")
    if filename.endswith(".py"):
        stem = filename[:-3]
    elif filename.endswith((".so", ".pyd")):
        stem = filename.split(".", 1)[0]
    else:
        return None
    module = parent.replace("/", ".") if stem == "__init__" else ".".join(filter(None, (parent.replace("/", "."), stem)))
    return module if module and all(part.isidentifier() for part in module.split(".")) else None


def _cott_installed_import_owners():
    owners = {}
    for distribution in _metadata.distributions():
        by_module = {}
        for relative in distribution.files or ():
            module = _cott_import_module_name(relative.as_posix())
            if module is not None:
                by_module.setdefault(module, []).append(relative)
        for module, origins in by_module.items():
            owners.setdefault(module, []).append((distribution, origins))
    return owners


def _cott_import_origin_trace(module):
    # FileFinder inspects ordinary installed files without importing a parent
    # package. util.find_spec would execute package initializers before they have
    # authenticated provenance. Namespace portions have no initializer to execute.
    search = list(_sys.path)
    trace = []
    prefix = []
    loaders = (
        (_machinery.ExtensionFileLoader, _machinery.EXTENSION_SUFFIXES),
        (_machinery.SourceFileLoader, _machinery.SOURCE_SUFFIXES),
        (_machinery.SourcelessFileLoader, _machinery.BYTECODE_SUFFIXES),
    )
    parts = module.split(".")
    for index, part in enumerate(parts):
        prefix.append(part)
        name = ".".join(prefix)
        namespaces = []
        concrete = None
        for directory in search:
            if not isinstance(directory, str):
                continue
            spec = _machinery.FileFinder(directory, *loaders).find_spec(name)
            if spec is None:
                continue
            if spec.loader is not None:
                concrete = spec
                break
            namespaces.extend(spec.submodule_search_locations or ())
        if concrete is not None:
            if not isinstance(concrete.origin, str):
                raise ValueError(f"external import {name!r} has no regular origin")
            if name in _sys.modules:
                loaded = _sys.modules[name]
                loaded_origin = getattr(loaded, "__file__", None)
                if not isinstance(loaded_origin, str) or _Path(loaded_origin).absolute() != _Path(concrete.origin).absolute():
                    raise ValueError(f"external import {name!r} is preloaded from a different origin")
                loaded_paths = getattr(loaded, "__path__", None)
                if concrete.submodule_search_locations is not None and (
                    loaded_paths is None
                    or [_Path(path).absolute() for path in loaded_paths]
                    != [_Path(path).absolute() for path in concrete.submodule_search_locations]
                ):
                    raise ValueError(f"external package {name!r} has a different loaded search path")
            trace.append((name, _Path(concrete.origin).absolute()))
            search = list(concrete.submodule_search_locations or ())
        elif namespaces:
            if name in _sys.modules:
                loaded = _sys.modules[name]
                loaded_paths = getattr(loaded, "__path__", None)
                if getattr(loaded, "__file__", None) is not None or loaded_paths is None or (
                    [_Path(path).absolute() for path in loaded_paths]
                    != [_Path(path).absolute() for path in namespaces]
                ):
                    raise ValueError(f"external namespace {name!r} has a different loaded search path")
            search = namespaces
            if index == len(parts) - 1:
                raise ValueError(f"external import {module!r} is an unowned namespace")
        else:
            return None
    return trace


def _cott_owned_external_imports(source, project_modules, owners=None):
    imports = set()
    stdlib = set(_sys.stdlib_module_names) | {"cott_runtime", "_cott_impl"}
    for node in _ast.walk(_ast.parse(source)):
        if isinstance(node, _ast.Import):
            imports.update(alias.name for alias in node.names if alias.name not in project_modules and alias.name.split(".", 1)[0] not in stdlib)
        elif isinstance(node, _ast.ImportFrom) and node.level == 0 and node.module:
            module = node.module
            if module in project_modules or module.split(".", 1)[0] in stdlib:
                continue
            for alias in node.names:
                child = module + "." + alias.name
                imports.add(child if _cott_import_origin_trace(child) is not None else module)
    if not imports:
        return []
    if owners is None:
        owners = _cott_installed_import_owners()
    resolved = []
    seen = set()
    for imported in sorted(imports):
        trace = _cott_import_origin_trace(imported)
        if trace is None:
            raise ValueError(f"external import {imported!r} has no installed origin")
        for module, actual in trace:
            if module in seen:
                continue
            seen.add(module)
            candidates = owners.get(module, ())
            if len(candidates) != 1:
                raise ValueError(f"external import {module!r} belongs to {len(candidates)} installed distributions")
            distribution, origins = candidates[0]
            if not any(_Path(distribution.locate_file(relative)).absolute() == actual for relative in origins):
                raise ValueError(f"external import {module!r} is shadowed outside its owning distribution")
            name = distribution.metadata.get("Name")
            if not isinstance(name, str) or not name:
                raise ValueError(f"external import {module!r} has no distribution identity")
            resolved.append((module, name.lower().replace("_", "-"), distribution, origins))
    return resolved
