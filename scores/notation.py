# compases = []
# with open("C:/Users/ferna/Dropbox/UC/Magister/robot-flautista/new_interface/scores/syrinx.txt", "r") as file:
#     for compas in file.readlines():
#         compases.append(compas.replace("\n", "()").replace(" ", "() "))

# with open("C:/Users/ferna/Dropbox/UC/Magister/robot-flautista/new_interface/scores/syrinx2.txt", "w") as file:
#     for compas in compases:
#         file.write(compas)
#         file.write("\n")

import mido
import json
from datetime import datetime

# new_compases = []
# with open("C:/Users/ferna/Dropbox/UC/Magister/robot-flautista/new_interface/scores/syrinx3.txt", "r") as file:
#     for compas in file.readlines():
#         notas = compas.replace("\n", "").split(" ")
#         new_compas = ""
#         for nota in notas:
#             # print(nota)
#             n, t = nota.replace(")","").split("(")
#             lit = []
#             num = []
#             if n[0] != "R":
#                 for char in n:
#                     if char.isnumeric():
#                         num.append(char)
#                     else:
#                         lit.append(char)
#                 new_note = "".join(lit) + num[0] + "(" + t + ")"
#             else:
#                 new_note = n + " " + t
#             new_compas += new_note
#             new_compas += " "
#         new_compas += "\n"
#         new_compases.append(new_compas)

# with open("C:/Users/ferna/Dropbox/UC/Magister/robot-flautista/new_interface/scores/syrinx2.txt", "w") as file:
#     for compas in new_compases:
#         file.write(compas)

# new_compases = []
# conver_bemol = {"Ab": "G#", "Bb": "A#", "Db": "C#", "Eb": "D#", "Gb": "F#"}
# with open("C:/Users/ferna/Dropbox/UC/Magister/robot-flautista/new_interface/scores/syrinx.txt", "r") as file:
#     for compas in file.readlines():
#         notas = compas.replace(" \n", "").split(" ")
#         new_compas = ""
#         for nota in notas:
#             print(nota)
#             n, t = nota.replace(")","").split("(")

#             if t == "0.5/3":
#                 new_t = str(0.5/3)
#             elif t == "1/3":
#                 new_t = str(1/3)
#             elif t == "2/3":
#                 new_t = str(2/3)
#             elif t == "2/5":
#                 new_t = str(2/5)
#             else:
#                 new_t = t

#             n_sin_num = n[:-1]
#             num_n = n[-1]
#             if "b" in n_sin_num:
#                 new_n = conver_bemol[n_sin_num] + num_n
#                 new_note = new_n + "(" + new_t + ")"
#             else:
#                 new_note = n + "(" + new_t + ")"

#             new_compas += new_note
#             new_compas += " "
#         new_compas += "\n"
#         new_compases.append(new_compas)

# with open("C:/Users/ferna/Dropbox/UC/Magister/robot-flautista/new_interface/scores/syrinx2.txt", "w") as file:
#     for compas in new_compases:
#         file.write(compas)

all_notes = ["C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3", "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4", "C5", "C#5", "D5", "D#5", "E5", "F5", "F#5", "G5", "G#5", "A5"]
notes_dic = {}
num = 48
for n in all_notes:
    notes_dic[n] = num
    num += 1

notes = []
with open("C:/Users/ferna/Dropbox/UC/Magister/robot-flautista/new_interface/scores/syrinx2.txt", "r") as file:
    time = 0
    for compas in file.readlines():
        notas = compas.replace(" \n", "").split(" ")
        
        for nota in notas:
            n, t = nota.replace(")","").split("(")
            if n != "R":
                notes.append([time, n])
                last_n = n
            else:
                notes.append([time, last_n])
            time += float(t)

print(notes)

# mid = mido.MidiFile()
# track = mido.MidiTrack()

# for n in notes:
#     track.append(mido.Message('note_on', note=n[0], velocity=64, time=0))
#     track.append(mido.Message('note_off', note=n[0], velocity=64, time=int(n[1]*1000)))
# mid.tracks.append(track)
# mid.save('C:/Users/ferna/Dropbox/UC/Magister/robot-flautista/new_interface/scores/archivo.mid')
