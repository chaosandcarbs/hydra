# hydra
A simple, python-based password manager using kivy. Portable for desktop and android. 

Create, read, and edit password files, and store them in an AES-encrypted container on disk. 

## Warnings
If you forget the password to decrypt a file, it is non-recoverable by design. 

### No, Really
Don't forget your password

## Running with .exe
I have working versions (for me) of a .exe (+ Installer) and Android APK file available on [Google Drive](https://drive.google.com/drive/folders/1XiMYEtU7TUfKFg8MLPEMdbtiZCadOnI_?usp=sharing).

### If you want to build your own .exe with PyInstaller
The [kivy website](https://kivy.org/doc/stable/guide/packaging-windows.html) has the best information (read it all - it will make your life simpler). 

You'll also need Visual Studio build tools for C++. They can be found on [Microsoft's website](https://visualstudio.microsoft.com/downloads/).

Lastly, you'll want to make sure you have the requisite packages;
```
python -m pip install --upgrade pip wheel setuptools
python -m pip install docutils pygments pypiwin32 
python -m pip install kivy.deps.sdl2 kivy.deps.glew kivy.deps.gstreamer
python -m pip install kivy.deps.angle
python -m pip install kivy kivy_examples
python -m pip install Pillow
python -m pip install cython
```

Building for Windows is currently using [PyInstaller](https://pyinstaller.org/en/stable/) (to turn the python3 code into a .exe), and a trial version of [Advanced Installer](https://www.advancedinstaller.com/) (to package everything up and create the installer file).

## Running on Android
If you install the APK file on your phone, you'll need to enable [developer options](https://developer.android.com/studio/debug/dev-options). Then you should be able to tap the APK using your file system app and install it (you may be prompted about installing apps from unknown sources). 

I plan to eventually get it on the Play Store...eventually...until then you'll have to manually install

### If you want to build your own APK with Buildozer
[Buildozer](https://buildozer.readthedocs.io/en/latest/ )'s documentation is pretty good, and should get you more than started.

You'll need some kind of 'nix (Linux/BSD/etc. type system) to build for Android. I'm doing it in Windows 10 using the Windows Subsystem for Linux (WSL) and Ubuntu 20.04. It's worth reading up on the [Buildozer Documentation for Windows 10](https://buildozer.readthedocs.io/en/latest/installation.html#targeting-android ) and the [Microsoft WSL documentation](https://docs.microsoft.com/en-us/windows/wsl/install).

## Running with Python 3
The hydra/ folder has the associated main.py and main.kv  (kivy) file. You'll want to make sure the following are installed first:

```
python -m pip install --upgrade pip wheel setuptools
python -m pip install functools kivy
```

Additionally, because this stores files AES-encrypted, you'll need either pycrpto or pycryptodome (either works):
```
python -m pip install pycryptodome
```

Just run the code like you would any other python script:
```
python main.py
```
