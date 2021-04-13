# -*- coding: UTF-8 -*-
import os
import os.path
import threading


class ResourcesManager:
    def __init__(self, path):
        self.path = os.path.normpath(path)
        self.locks = {}
    
    def write(self, path, data, mkdir=False):
        if os.path.isdir(path):
            raise ValueError(f"Cannot write to {path} for it is a directory!")

        path = self.path + "/" + os.path.normpath(path)

        if ".." in path or path[0] == "/":
            raise ValueError("Only relative paths to childs are allowed!")

        if mkdir:
            subdirs = os.path.normpath(path).split('/')
            del subdirs[-1]
            os.makedirs('/'.join(subdirs), exist_ok=True)

        if not (path in self.locks.keys()):
            self.locks[path] = threading.Lock()

        
        with self.locks[path]:
            with open(path, 'w') as file:
                file.write(data)

        
    def read(self, path):
        path = self.path + "/" + os.path.normpath(path)

        if os.path.isdir(path):
            raise IsADirectoryError(f"Cannot write to {path} for it is a directory!")

        if ".." in path or path[0] == "/":
            raise ValueError("Only relative paths to childs are allowed!")

        if not os.path.isfile(path):
            raise FileNotFoundError(f"{path} does not exist!")

        data = None

        if not (path in self.locks.keys()):
            self.locks[path] = threading.Lock()

        with self.locks[path]:
            with open(path, 'r') as file:
                data = file.read()
        
        return data

    def delete(self, path):
        path = self.path + '/' + path
        
        if os.path.isdir(path):
            raise IsADirectoryError(f"Cannot delete to {path} for it is a directory!\nTo delete a directory, use ResourcesManager.delete_dir(path)")

        if ".." in path or path[0] == "/":
            raise ValueError("Only relative paths to childs are allowed!")

        if not os.path.isfile(path):
            raise FileNotFoundError(f"{path} does not exist!")
        
        os.remove(path)
    
    def delete_dir(self, path):
        
        if os.path.isfile(path):
            raise ValueError(f"Cannot delete to {path} for it is a file!\nTo delete a file, use ResourcesManager.delete(path)")

        if ".." in path or path[0] == "/":
            raise ValueError("Only relative paths to childs are allowed!")

        path = self.path + '/' + path

        if not os.path.isdir(path):
            raise FileNotFoundError(f"{path} does not exist!")
        
        os.rmdir(path)