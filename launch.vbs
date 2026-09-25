' launch.vbs — start RightDock hidden (no console window)
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = "pythonw.exe"

' Run pythonw main.py from the project folder, window state 0 (hidden)
shell.CurrentDirectory = projectDir
shell.Run """" & pythonw & """ """ & projectDir & "\main.py""", 0, False