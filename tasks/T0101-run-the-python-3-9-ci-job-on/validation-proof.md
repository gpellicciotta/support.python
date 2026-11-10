## Walkthrough & Validation

Red phase, GitHub CI run 42843923273 (3.9 on `ubuntu-latest`):
```text
Version 3.9 was not found in the local cache
##[error]The version '3.9' with architecture 'x64' was not found for Ubuntu 26.04.
exit=1
```

After the runner pin, run 42862112611 installed 3.9 and ran the suite; T0102 fixed the 18 failures it exposed.
Green phase, GitHub CI run 42863145089 on 9a87805:
```text
build (3.9, ubuntu-24.04) | Successfully built support-python
build (3.9, ubuntu-24.04) | All checks passed!
build (3.9, ubuntu-24.04) | 1204 passed, 7 skipped in 52.64s
build (3.9, ubuntu-24.04) | Successfully built support_python-2.0.8rc0.tar.gz and support_python-2.0.8rc0-py3-none-any.whl
build (3.x, ubuntu-latest) | Successfully built support-python
build (3.x, ubuntu-latest) | All checks passed!
build (3.x, ubuntu-latest) | 1204 passed, 7 skipped, 191 subtests passed in 33.51s
build (3.x, ubuntu-latest) | Successfully built support_python-2.0.8rc0.tar.gz and support_python-2.0.8rc0-py3-none-any.whl
exit=0
```
