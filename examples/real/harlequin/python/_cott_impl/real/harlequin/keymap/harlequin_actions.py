from cott_runtime import CottList

from real.harlequin.keymap_types import ActionScope, ActionScope_App, ActionScope_Catalog, ActionScope_ContextMenu, ActionScope_Editor, ActionScope_Results, ActionSpec


def _scope_name(scope: ActionScope) -> str:
    if isinstance(scope, ActionScope_App):
        return "App"
    if isinstance(scope, ActionScope_Editor):
        return "Editor"
    if isinstance(scope, ActionScope_Catalog):
        return "Catalog"
    if isinstance(scope, ActionScope_ContextMenu):
        return "ContextMenu"
    if isinstance(scope, ActionScope_Results):
        return "Results"
    return "History"


def harlequin_actions(scope: ActionScope) -> CottList[ActionSpec]:
    rows: list[str] = [
        "quit|App|Quit|1|1",
        "help|App|Help|1|0",
        "focus_next|App|Focus Next|0|0",
        "focus_previous|App|Focus Previous|0|0",
        "focus_query_editor|App|Focus Query Editor|0|0",
        "focus_results_viewer|App|Focus Results Viewer|0|0",
        "focus_data_catalog|App|Focus Data Catalog|0|0",
        "toggle_sidebar|App|Toggle Sidebar|0|0",
        "toggle_full_screen|App|Toggle Full Screen|0|0",
        "show_debug_info|App|Debug Info|0|0",
        "show_query_history|App|History|1|0",
        "show_data_exporter|App|Export Data|0|0",
        "refresh_catalog|App|Refresh Data Catalog|0|0",
        "run_query|App|Run Query|0|0",
        "cancel_query|App|Cancel Query|0|0",
        "code_editor.new_buffer|Editor|New Buffer|0|0",
        "code_editor.close_buffer|Editor|Close Buffer|0|0",
        "code_editor.next_buffer|Editor|Next Buffer|0|0",
        "code_editor.run_query|Editor|Run Query|1|0",
        "code_editor.format_buffer|Editor|Format Query|1|0",
        "code_editor.save_buffer|Editor|Save Query|1|0",
        "code_editor.load_buffer|Editor|Open Query|1|0",
        "code_editor.launch_external_editor|Editor|Launch External Editor|0|0",
        "code_editor.find|Editor|Find|1|0",
        "code_editor.find_next|Editor|Find Next|1|0",
        "code_editor.goto_line|Editor|Go To Line|1|0",
        "code_editor.cursor_up|Editor|Cursor Up|0|0",
        "code_editor.cursor_down|Editor|Cursor Down|0|0",
        "code_editor.cursor_left|Editor|Cursor Left|0|0",
        "code_editor.cursor_right|Editor|Cursor Right|0|0",
        "code_editor.cursor_word_left|Editor|Cursor Word Left|0|0",
        "code_editor.cursor_word_right|Editor|Cursor Word Right|0|0",
        "code_editor.cursor_line_start|Editor|Cursor Line Start|0|0",
        "code_editor.cursor_line_end|Editor|Cursor Line End|0|0",
        "code_editor.cursor_doc_start|Editor|Cursor Doc Start|0|0",
        "code_editor.cursor_doc_end|Editor|Cursor Doc End|0|0",
        "code_editor.cursor_page_up|Editor|Cursor Page Up|0|0",
        "code_editor.cursor_page_down|Editor|Cursor Page Down|0|0",
        "code_editor.select_up|Editor|Select Up|0|0",
        "code_editor.select_down|Editor|Select Down|0|0",
        "code_editor.select_left|Editor|Select Left|0|0",
        "code_editor.select_right|Editor|Select Right|0|0",
        "code_editor.select_word_left|Editor|Select Word Left|0|0",
        "code_editor.select_word_right|Editor|Select Word Right|0|0",
        "code_editor.select_line_start|Editor|Select Line Start|0|0",
        "code_editor.select_line_end|Editor|Select Line End|0|0",
        "code_editor.select_doc_start|Editor|Select Doc Start|0|0",
        "code_editor.select_doc_end|Editor|Select Doc End|0|0",
        "code_editor.select_word|Editor|Select Word|0|0",
        "code_editor.select_line|Editor|Select Line|0|0",
        "code_editor.select_all|Editor|Select All|0|0",
        "code_editor.scroll_up_one|Editor|Scroll Up One|0|0",
        "code_editor.scroll_down_one|Editor|Scroll Down One|0|0",
        "code_editor.toggle_comment|Editor|Toggle Comment|0|0",
        "code_editor.cut|Editor|Cut|0|0",
        "code_editor.copy|Editor|Copy|0|0",
        "code_editor.paste|Editor|Paste|0|0",
        "code_editor.undo|Editor|Undo|0|0",
        "code_editor.redo|Editor|Redo|0|0",
        "code_editor.delete_left|Editor|Delete Left|0|0",
        "code_editor.delete_right|Editor|Delete Right|0|0",
        "code_editor.delete_word_left|Editor|Delete Word Left|0|0",
        "code_editor.delete_word_right|Editor|Delete Word Right|0|0",
        "code_editor.delete_line|Editor|Delete Line|0|0",
        "code_editor.delete_to_start_of_line|Editor|Delete To Start Of Line|0|0",
        "code_editor.delete_to_end_of_line|Editor|Delete To End Of Line|0|0",
        "code_editor.focus_results_viewer|Editor|Focus Results Viewer|0|0",
        "code_editor.focus_data_catalog|Editor|Focus Data Catalog|0|0",
        "data_catalog.previous_tab|Catalog|Previous Tab|0|0",
        "data_catalog.next_tab|Catalog|Next Tab|0|0",
        "data_catalog.insert_name|Catalog|Insert Name|1|0",
        "data_catalog.copy_name|Catalog|Copy Name|0|0",
        "data_catalog.select_cursor|Catalog|Select Cursor|0|0",
        "data_catalog.toggle_node|Catalog|Toggle Node|0|0",
        "data_catalog.cursor_up|Catalog|Cursor Up|0|0",
        "data_catalog.cursor_down|Catalog|Cursor Down|0|0",
        "data_catalog.focus_query_editor|Catalog|Focus Query Editor|0|0",
        "data_catalog.focus_results_viewer|Catalog|Focus Results Viewer|0|0",
        "data_catalog.show_context_menu|Catalog|Show Context Menu|1|0",
        "data_catalog.hide_context_menu|ContextMenu|Hide Context Menu|0|0",
        "results_viewer.previous_tab|Results|Previous Tab|0|0",
        "results_viewer.next_tab|Results|Next Tab|0|0",
        "results_viewer.copy_selection|Results|Copy Selection|0|0",
        "results_viewer.view_cell|Results|View Cell|0|0",
        "results_viewer.select_cursor|Results|Select Cursor|0|0",
        "results_viewer.cursor_up|Results|Cursor Up|0|0",
        "results_viewer.cursor_down|Results|Cursor Down|0|0",
        "results_viewer.cursor_left|Results|Cursor Left|0|0",
        "results_viewer.cursor_right|Results|Cursor Right|0|0",
        "results_viewer.cursor_row_start|Results|Cursor Row Start|0|0",
        "results_viewer.cursor_row_end|Results|Cursor Row End|0|0",
        "results_viewer.cursor_column_start|Results|Cursor Column Start|0|0",
        "results_viewer.cursor_column_end|Results|Cursor Column End|0|0",
        "results_viewer.cursor_next_cell|Results|Cursor Next Cell|0|0",
        "results_viewer.cursor_previous_cell|Results|Cursor Previous Cell|0|0",
        "results_viewer.cursor_page_up|Results|Cursor Page Up|0|0",
        "results_viewer.cursor_page_down|Results|Cursor Page Down|0|0",
        "results_viewer.cursor_table_start|Results|Cursor Table Start|0|0",
        "results_viewer.cursor_table_end|Results|Cursor Table End|0|0",
        "results_viewer.select_up|Results|Select Up|0|0",
        "results_viewer.select_down|Results|Select Down|0|0",
        "results_viewer.select_left|Results|Select Left|0|0",
        "results_viewer.select_right|Results|Select Right|0|0",
        "results_viewer.select_row_start|Results|Select Row Start|0|0",
        "results_viewer.select_row_end|Results|Select Row End|0|0",
        "results_viewer.select_column_start|Results|Select Column Start|0|0",
        "results_viewer.select_column_end|Results|Select Column End|0|0",
        "results_viewer.select_page_up|Results|Select Page Up|0|0",
        "results_viewer.select_page_down|Results|Select Page Down|0|0",
        "results_viewer.select_table_start|Results|Select Table Start|0|0",
        "results_viewer.select_table_end|Results|Select Table End|0|0",
        "results_viewer.select_all|Results|Select All|0|0",
        "results_viewer.focus_query_editor|Results|Focus Query Editor|0|0",
        "results_viewer.focus_data_catalog|Results|Focus Data Catalog|0|0",
        "history_screen.select_query|History|Select Query|1|1",
        "history_screen.toggle_filters|History|Filter|1|0",
        "history_screen.cancel|History|Cancel|1|0",
    ]
    wanted = _scope_name(scope)
    specs: list[ActionSpec] = []
    for index, row in enumerate(rows):
        parts = row.split("|")
        if parts[1] != wanted:
            continue
        specs.append(ActionSpec(name=parts[0], scope=scope, description=parts[2], show=parts[3] == "1", priority=parts[4] == "1", position=index))
    return CottList(values=specs)
