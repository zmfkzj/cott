//! Compiler-owned Linux process-control restriction, installed before secret input.
//! Landlock is already inherited from the single-threaded compiler launcher.
#[cfg(all(
    target_os = "linux",
    any(target_arch = "x86_64", target_arch = "aarch64")
))]
pub fn install() -> Result<(), String> {
    use std::ffi::c_long;
    #[repr(C)]
    struct Filter {
        code: u16,
        jt: u8,
        jf: u8,
        k: u32,
    }
    #[repr(C)]
    struct Program {
        len: u16,
        filter: *const Filter,
    }
    unsafe extern "C" {
        fn syscall(number: c_long, ...) -> c_long;
    }
    #[cfg(target_arch = "x86_64")]
    const NUMBERS: (u32, c_long, u32, u32, u32, u32, &[u32]) = (
        0xc000003e,
        317,
        59,
        322,
        56,
        435,
        &[57, 58, 101, 310, 311, 438],
    );
    #[cfg(target_arch = "aarch64")]
    const NUMBERS: (u32, c_long, u32, u32, u32, u32, &[u32]) =
        (0xc00000b7, 277, 221, 281, 220, 435, &[117, 270, 271, 438]);
    const LOAD: u16 = 0x20;
    const EQ: u16 = 0x15;
    const SET: u16 = 0x45;
    const RET: u16 = 0x06;
    const ALLOW: u32 = 0x7fff0000;
    const DENY: u32 = 0x00050001;
    const UNSUPPORTED: u32 = 0x00050026;
    const KILL: u32 = 0x80000000;
    let mut filter = vec![
        Filter {
            code: LOAD,
            jt: 0,
            jf: 0,
            k: 4,
        },
        Filter {
            code: EQ,
            jt: 1,
            jf: 0,
            k: NUMBERS.0,
        },
        Filter {
            code: RET,
            jt: 0,
            jf: 0,
            k: KILL,
        },
        Filter {
            code: LOAD,
            jt: 0,
            jf: 0,
            k: 0,
        },
    ];
    #[cfg(target_arch = "x86_64")]
    filter.extend([
        Filter {
            code: SET,
            jt: 0,
            jf: 1,
            k: 0x40000000,
        },
        Filter {
            code: RET,
            jt: 0,
            jf: 0,
            k: UNSUPPORTED,
        },
    ]);
    for number in [NUMBERS.2, NUMBERS.3]
        .into_iter()
        .chain(NUMBERS.6.iter().copied())
    {
        filter.extend([
            Filter {
                code: EQ,
                jt: 0,
                jf: 1,
                k: number,
            },
            Filter {
                code: RET,
                jt: 0,
                jf: 0,
                k: DENY,
            },
        ]);
    }
    // glibc falls back from clone3 ENOSYS to clone; only CLONE_THREAD is allowed.
    filter.extend([
        Filter {
            code: EQ,
            jt: 0,
            jf: 1,
            k: NUMBERS.5,
        },
        Filter {
            code: RET,
            jt: 0,
            jf: 0,
            k: UNSUPPORTED,
        },
        Filter {
            code: EQ,
            jt: 0,
            jf: 3,
            k: NUMBERS.4,
        },
        Filter {
            code: LOAD,
            jt: 0,
            jf: 0,
            k: 16,
        },
        Filter {
            code: SET,
            jt: 1,
            jf: 0,
            k: 0x00010000,
        },
        Filter {
            code: RET,
            jt: 0,
            jf: 0,
            k: DENY,
        },
        Filter {
            code: RET,
            jt: 0,
            jf: 0,
            k: ALLOW,
        },
    ]);
    let program = Program {
        len: u16::try_from(filter.len()).map_err(|_| "seccomp filter length overflow")?,
        filter: filter.as_ptr(),
    };
    // SET_MODE_FILTER + TSYNC: fail closed if any thread cannot receive the policy.
    let result = unsafe { syscall(NUMBERS.1, 1u32, 1u32, &program as *const Program) };
    if result != 0 {
        return Err(format!(
            "install Rust runtime seccomp TSYNC: {} (result {result})",
            std::io::Error::last_os_error()
        ));
    }
    Ok(())
}
#[cfg(not(all(
    target_os = "linux",
    any(target_arch = "x86_64", target_arch = "aarch64")
)))]
pub fn install() -> Result<(), String> {
    Err("Rust verification requires Linux x86_64/aarch64 process confinement".into())
}
