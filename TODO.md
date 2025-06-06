# TODO

## P1
- remove comments/print statements
- cross build testing
    - build on modal run on modal
    - build on ubuntu box, run on box
    - build on modal, tar it, run on ubuntu box
    - build on modal, tar it, run on 22.04
    - test build that starts on python 3.9
    - same test with int4
    - optional(?) build in ubuntu box, tar it, run on modal
- review diff
- think of more tests for the fix
- make test list on PR

## P2
- add modal deploy script
    - add args where it automatically also runs the build.sh script with an example


## P3
- Look into adding uv/make pip install faster?
- Package a demo image to the user.
- Add better image propagation
- Spinner doesn't get killed even if you Ctrl+C?
- Need "clear" command in cli.
- Add functionality to query a non-local image.
- Add README for devs who want to get into the code because it's a mess to understand.
- How can I make the code more readable?
- A lot of code that does different things has similar naming.
- There seems to be some redundant code.
