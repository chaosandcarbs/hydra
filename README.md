# hydra
A simple, python-based password manager using kivy. Portable for desktop and android. 

Create, read, and edit password files, and store them in an AES-encrypted container on disk. 

## Warnings
If you forget the password to decrypt a file, it is non-recoverable by design. 

## Running with .exe
The executable included in the dist/ folder works on my machine :)

## Running with Python 3
The hydra/ folder has the associated hydra.py and hydra.kv  (kivy) file. You'll want to make sure the following are installed first:

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
python hydra.py
```

### If you want to build your own .exe with PyInstaller
The kivy website has the best information (read it all - it will make your life simpler). 
> https://kivy.org/doc/stable/guide/packaging-windows.html 

You'll also need Visual Studio build tools for C++ :
> https://visualstudio.microsoft.com/downloads/

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
