import pyttsx3

engine = pyttsx3.init()
voces = engine.getProperty('voices')

print("=========================================")
print("   VOCES INSTALADAS EN TU COMPUTADORA    ")
print("=========================================")

for i, voz in enumerate(voces):
    print(f"ID [{i}]: {voz.name}")
    
print("=========================================")