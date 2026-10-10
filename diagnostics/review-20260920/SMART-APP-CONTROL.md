# Smart App Control diagnosis, September 20, 2026

The inspected Code Integrity events (3077/3118, about 11:23 local time) named
`goproverbs/target/debug/deps/goproverbs-d5059b207cb5e26e.exe`, launched by Cargo.
Authenticode inspection reported NotSigned. This was a generated Rust test
executable in the separate goproverbs work, not the Pi benchmark executable.

Microsoft documents that Smart App Control can accept signatures using an RSA
code-signing certificate issued by a trusted provider. A self-signed development
certificate does not satisfy that requirement. Signing Cargo alone would not
sign the test programs Cargo builds.

To keep testing native Windows binaries with this route, obtain an eligible
trusted signing service or certificate and arrange build -> sign -> run for
each freshly built executable (including test executables). SignTool can perform
the signing. Certificate enrollment, credentials, and any purchase remain to be
arranged; no signing identity was available in the inspected session store.
That store check does not establish the absence of identities in other stores
or accounts.

For development, a Linux build/test workflow under WSL is another option to
assess. It would not validate Windows-specific behavior. No WSL migration,
certificate enrollment, or Windows security-setting changes were performed.

Sources checked September 20:

- [Microsoft explanation of this block](https://support.microsoft.com/en-us/windows/security/threat-malware-protection/smart-app-control-has-blocked-part-of-this-app)
- [Signing requirements and SignTool](https://learn.microsoft.com/en-us/windows/apps/develop/smart-app-control/code-signing-for-smart-app-control)
- [Code-signing options](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)
