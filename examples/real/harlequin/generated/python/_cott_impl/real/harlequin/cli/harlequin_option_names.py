from cott_runtime import CottList


def harlequin_option_names() -> CottList[str]:
    return CottList(
        values=[
            "adapter",
            "conn_str",
            "keymap_name",
            "limit",
            "locale",
            "no_download_tzdata",
            "no_write_history",
            "output",
            "read_only",
            "show_files",
            "show_s3",
            "ssh_allow_reuse",
            "ssh_batch_mode",
            "ssh_forward",
            "ssh_host",
            "ssh_timeout",
            "theme",
            "viewer_max_rows",
        ]
    )
