fn main() {
    let arguments = std::env::args_os().collect::<Vec<_>>();
    if let Some(status) = cott::sandbox::landlock::dispatch(&arguments) {
        std::process::exit(status);
    }
    std::process::exit(cott::cli::run(arguments));
}
