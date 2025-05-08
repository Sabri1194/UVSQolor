import numpy as np
import tkinter as tk
from tkinter import filedialog,messagebox
from PIL import Image
from PIL import ImageTk 
from scipy.signal import convolve2d

# Définition des variables globales
nom_fichier=None
photo=None
canvas=None
matrice=None
historique = [matrice]

# Gestion de l'affichage
def rafraichir(ajouter_historique=True):
    global photo, matrice
    image = Image.fromarray(matrice)
    photo = ImageTk.PhotoImage(image)

    canvas.config(width=photo.width(), height=photo.height())  # redimensionner AVANT
    canvas.delete('all')
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.image = photo

    if ajouter_historique:
        historique.append(matrice.copy())


def applique_effet():
    global matrice_2
    matrice_2 = matrice.copy()
    rafraichir(ajouter_historique=True)
    dialogue_effet.destroy()

def annule_effet():
    global matrice
    matrice = matrice_2.copy()
    rafraichir()
    dialogue_effet.destroy()

def undo_effet():
    global matrice, historique
    if len(historique) > 1:
        historique.pop()
        matrice = historique[-1].copy()
        rafraichir(ajouter_historique=False)
    else:
        messagebox.showinfo("Info", "Aucun effet à annuler")

# Algorithmes de filtre
def filtre_vert():
    global matrice
    matrice[:,:,[0,2]]=0

def filtre_gris():
    """cette fonction rend les tuples de 3 (R,G,B)
      en 1 valeurs de gris selon les sensibilité humaine aux couleurs"""
    global matrice
    for i in range (matrice.shape[0]):
        for j in range (matrice.shape[1]):
            r,g,b = matrice[i,j]
            gris=int(0.2125*r+0.7154*g+0.0721*b)
            matrice[i,j]= [gris,gris,gris]
    matrice= matrice.astype(np.uint8)


def correction_gamma(facteur):
    global photo, matrice

    gamma = 1 / float(facteur)
    matrice_float = matrice_2.astype(np.float32)
    max_value = float(np.iinfo(matrice.dtype).max)
    for i in range(matrice.shape[0]):
        for j in range(matrice.shape[1]):
            for c in range(3):  # canal 0=R, 1=G, 2=B
                val_in = matrice_float[i, j, c] / max_value
                val_out = pow(val_in, float(gamma))
                matrice_float[i, j, c] = max_value * val_out

    matrice = matrice_float.clip(0, max_value).astype(np.uint8)
    rafraichir(ajouter_historique=True)

def correction_sigmoide(c,k):
    global matrice, matrice_2
    k=float(k)
    c=float(c)
    matrice_float= matrice_2.astype(np.float32)
    max_value= float(np.iinfo(matrice.dtype).max)
    for i in range(matrice.shape[0]):
        for j in range(matrice.shape[1]):
            for d in range(3):
                val_in= matrice_float[i,j,d]/max_value
                val_out= 1/(1+np.exp(-k*(val_in-0.5)*c))
                matrice_float[i,j,d]=val_out*max_value
    matrice = matrice_float.clip(0, max_value).astype(np.uint8)
    rafraichir(ajouter_historique=True)

def convoleve2d(matrice, kernel, mode='same',boundary='symm'):
            for i in range(3):
                image_2d = matrice[:, :, i]
                image_flou = convolve2d(image_2d, kernel, mode=mode, boundary=boundary)
                image_flou = np.clip(image_flou, 0, 255).astype(np.uint8)
                matrice[:, :, i] = image_flou

                
# Callbacks
def cb_ouvrir():
    global nom_fichier, photo, canvas, matrice,matrice_2
    nom_fichier=filedialog.askopenfilename(title='Ouvrir une image')
    if nom_fichier is not None:
        img=Image.open(nom_fichier)
        matrice=np.array(img)
        matrice_2= matrice.copy()
        menu_effets.entryconfig('Vert',state=tk.NORMAL)
        menu_effets.entryconfig("Gris",state=tk.NORMAL)
        menu_effets.entryconfig("luminosité",state=tk.NORMAL)
        menu_effets.entryconfig("Contraste",state=tk.NORMAL)
        menu_effets.entryconfig("Flou",state=tk.NORMAL)
        menu_effets.entryconfig("Annuler",state=tk.NORMAL)
        historique.clear()
        historique.append(matrice.copy())
        rafraichir()
        
        
def cb_vert():
    filtre_vert()
    rafraichir(ajouter_historique=True)

def cb_gris():
    filtre_gris()
    rafraichir(ajouter_historique=True)

def cb_lumi():
    global dialogue_effet
    dialogue_effet = tk.Toplevel(fenetre_principale)
    dialogue_effet.title("Luminosité")
    dialogue_effet.geometry("300x150")
    dialogue_effet.grab_set()
    slider = tk.Scale(dialogue_effet, from_=0.1, to=3.0,
                      orient=tk.HORIZONTAL, length=200,
                      resolution=0.1, digits=2,
                      command=correction_gamma)
    slider.set(1.0)
    slider.pack(pady=20)

    frame_boutons = tk.Frame(dialogue_effet)
    frame_boutons.pack(side=tk.BOTTOM, pady=10)

    bouton_appliquer = tk.Button(frame_boutons, text="Appliquer",
                                 command=applique_effet)
    bouton_appliquer.pack(side=tk.LEFT, padx=10)

    bouton_annuler = tk.Button(frame_boutons, text="Annuler",
                               command=annule_effet)
    bouton_annuler.pack(side=tk.LEFT, padx=10)

def cb_contraste():
    """créer les slider de contraste et de pente"""
    global dialogue_effet
    dialogue_effet = tk.Toplevel(fenetre_principale)
    dialogue_effet.title("Contraste")
    dialogue_effet.geometry("300x300")
    dialogue_effet.grab_set()
    slider1 = tk.Scale(dialogue_effet, from_=0.1, to=3.0,
                      orient=tk.HORIZONTAL, length=200,
                      resolution=0.1, digits=3,
                      command=lambda x: correction_sigmoide(slider1.get(), slider2.get()))
    slider1.set(1.0)
    slider1.pack(pady=20)


    slider2 = tk.Scale(dialogue_effet, from_=0.1, to=20.0,
                      orient=tk.HORIZONTAL, length=200,
                      resolution=1.0, digits=2,
                      command=lambda x: correction_sigmoide(slider1.get(), slider2.get()))

    slider2.set(10.0)
    slider2.pack(pady=20)

    frame_boutons = tk.Frame(dialogue_effet)
    frame_boutons.pack(side=tk.BOTTOM, pady=10)

    bouton_appliquer = tk.Button(frame_boutons, text="Appliquer",
                                 command=applique_effet)
    bouton_appliquer.pack(side=tk.LEFT, padx=10)

    bouton_annuler = tk.Button(frame_boutons, text="Annuler",
                               command=annule_effet)
    bouton_annuler.pack(side=tk.LEFT, padx=10)


def cb_flou():
    kernel = np.ones((3, 3)) / 9
    convoleve2d(matrice,kernel)

    rafraichir(ajouter_historique=True)

# Création de la fenêtre principale
fenetre_principale=tk.Tk()
fenetre_principale.title('UVSQolor')
canvas=tk.Canvas(fenetre_principale)
canvas.pack()

menu_principal=tk.Menu(fenetre_principale)
fenetre_principale.config(menu=menu_principal)

menu_fichier=tk.Menu(menu_principal,tearoff=0)
menu_principal.add_cascade(label='Fichier', menu=menu_fichier)
menu_fichier.add_command(label='Ouvrir',command=cb_ouvrir)

menu_effets=tk.Menu(menu_principal,tearoff=0)
menu_principal.add_cascade(label='Effets', menu=menu_effets)
menu_effets.add_command(label='Vert',command=cb_vert,state=tk.DISABLED)
menu_effets.add_command(label="Gris", command= cb_gris,state=tk.DISABLED)
menu_effets.add_command(label="luminosité", command= cb_lumi,state= tk.DISABLED)
menu_effets.add_command(label="Contraste", command= cb_contraste,state= tk.DISABLED)
menu_effets.add_command(label="Flou", command= cb_flou,state= tk.DISABLED)
menu_effets.add_command(label="Annuler",command=undo_effet,state=tk.DISABLED)

fenetre_principale.mainloop()