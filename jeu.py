import arcade
import cv2

# Parametre de la fenetre
largeurFenetre = 640
hauteurFenetre = 420
titreFenetre = "Jeu-Platforme"

# modele d'entrainement 
teteCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# capture la webcam
captureVideo = cv2.VideoCapture(0)

# couleur des lignes dans la webcam
couleur = (255,0,0)

# Taille de nos sprites
tailleTuile = 0.5

# parametres du personnage 
graviter = 0.4
vitesseDeplacement = 1
vitesseAnimation = 10

# Permet de savoir si le personnage est sur le coté droit ou gauche
faceDroite = 0
faceGauche = 1


# Le nombre de pixels à conserver comme marge minimale entre le personnage et le bord de l'écran.
margeFenetreDroite = 250
margeFenetreBas = 0
margeFenetreHaut = 100

# Chargement des textures
def chargerTexture(filename):
    return [
        # Partie droite
        arcade.load_texture(filename),
        # Partie Gauche 
        arcade.load_texture(filename, flipped_horizontally=True)
    ]

class Personnage(arcade.Sprite):
    def __init__(self):
        super().__init__()
        # Mettre par default la face droite du personnage 
        self.personnageFaceDirection = faceDroite

        # va permetre de basculer entre les differentes images
        self.textureActuelle = 0

        # Hitbox du perssonage
        self.points = [[-10, -10], [10, -10], [10, 22], [-10, 22]]

        # Chargement des textures

        # Sprites
        sprites = "sprites/"

        # Chargement des textures pour se déplacer
        self.textureMarche = []
        for i in range(5):
            texture = chargerTexture(f"{sprites}r{i+1}.png")
            self.textureMarche.append(texture)


    def update_animation(self, delta_time: float = 1/34):
        # permet de savoir si on doit etre sur la face gauche ou celle de droite
        if self.change_x < 0 and self.personnageFaceDirection == faceDroite:
            self.personnageFaceDirection = faceGauche
        elif self.change_x > 0 and self.personnageFaceDirection == faceGauche:
            self.personnageFaceDirection = faceDroite

        # animation du deplacement
        self.textureActuelle += 1
        if self.textureActuelle > 4 * vitesseAnimation:
            self.textureActuelle = 0
        frame = self.textureActuelle // vitesseAnimation
        direction = self.personnageFaceDirection
        self.texture = self.textureMarche[frame][direction]


class VictoireView(arcade.View):
    # la "view" Victoire 

    def __init__(self):
        # lance le code des qu'on arrive cette view
        super().__init__()
        self.texture = arcade.load_texture("victoire.jpg")

        # on reset la position de la camera pour que l'image de fin soit bien au centre
        arcade.set_viewport(0, largeurFenetre - 1, 0, hauteurFenetre - 1)

    def on_draw(self):
        # afficher la view
        arcade.start_render()
        self.texture.draw_sized(largeurFenetre / 2, hauteurFenetre / 2,
                                largeurFenetre, hauteurFenetre)
    # relancer la partie qu'on on clique sur "R"
    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            game_view = JeuView()
            game_view.setup()
            self.window.show_view(game_view)
            
        
class JeuView(arcade.View):
    #Le jeu

    def setup(self):
        # Permet de suivre le defillement de la cam
        self.vueBas = 0
        self.vueGauche = 0

        # Créer les sprites list
        self.listePersonnage = arcade.SpriteList()

        self.personnage = Personnage()
        self.listeMurs = arcade.SpriteList()
        self.listePieges = arcade.SpriteList()
        self.listeCoffres = arcade.SpriteList()	

        self.tailleBackground = 10
        self.calquesBackground = ["self.bc0","self.bc1","self.bc2","self.bc3","self.bc4","self.bc5","self.bc6","self.bc7","self.bc8","self.bc9"]
        for i in range(self.tailleBackground):
        	self.calquesBackground[i] = arcade.SpriteList()

        self.personnage.center_x = 80
        self.personnage.center_y = 40

        self.listePersonnage.append(self.personnage)
        ### Chargement de la map sur tiled ###

        # Nom de la map tiled a charger
        nomMap = "map2.tmx"
        # Noms des calques de la map faite sur tiled que l'on va récuperer
        calqueMur = "Platforms"
        calquePieges = "Piques"
        calqueCoffres = "Coffre"

        # lire la map tiled
        mapTiled = arcade.tilemap.read_tmx(nomMap)

        # on set les murs, les murs vont représenté tout les blocs physique que l'on ne peu traversser
        self.listeMurs = arcade.tilemap.process_layer(map_object=mapTiled, layer_name=calqueMur, scaling=tailleTuile, use_spatial_hash=True)

        # on set la liste des pieges
        self.listePieges = arcade.tilemap.process_layer(mapTiled, calquePieges, tailleTuile)

        # on set la liste des coffres
        self.listeCoffres = arcade.tilemap.process_layer(mapTiled, calqueCoffres, tailleTuile)

        for i in range(self.tailleBackground):
        	self.calquesBackground[i] = arcade.tilemap.process_layer(mapTiled, str(i), tailleTuile)

        # intialiser le background color
        if mapTiled.background_color:
            arcade.set_background_color(mapTiled.background_color)

        # Créer le moteur phisyque qui va gérer les collision
        self.moteurPhysique = arcade.PhysicsEnginePlatformer(self.personnage, self.listeMurs, graviter)
        
    def on_draw(self):
        # Clear the screen to the background color
        arcade.start_render()

        # Afficher les textures background
        for i in range(self.tailleBackground):
        	self.calquesBackground[i].draw()

        # Afficher nos sprites
        self.listeMurs.draw()
        self.listePieges.draw()
        self.listeCoffres.draw()
        self.listePersonnage.draw()

    def on_update(self, delta_time):
        ### Partie Opencv ###
        _, image = captureVideo.read()

        # metre l'image en gris
        gris = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # détecter les têtes
        faces = teteCascade.detectMultiScale(gris, 1.1, 4)

        # Dessiner un carer autour de chaque tête
        for (x, y, w, h) in faces:
            ### Deplacement de personnage ###
             # Partie jump droite
            if (x<325 and y<250):
                self.personnage.change_x = vitesseDeplacement
                if self.moteurPhysique.can_jump():
                    self.personnage.change_y = 7

            # Partie jump gauche
            if (x>325 and y<250):
                self.personnage.change_x = -vitesseDeplacement
                if self.moteurPhysique.can_jump():
                    self.personnage.change_y = 7

            # Partie a gauche
            if (x>325 and y>250):
                self.personnage.change_x = -vitesseDeplacement

            # Partie a Droite    
            if (x<325 and y>250):
                self.personnage.change_x = vitesseDeplacement
            # dessin du carer
            cv2.rectangle(image, (x, y), (x+w, y+h), couleur, 2)

        #on renversse l'image
        image = cv2.flip(image, 1)

        # dessin du background    
        cv2.line(image,(325,500),(325,0),couleur,5)
        cv2.line(image,(750,250),(0,250),couleur,5)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(image,'Gauche',(10,400), font, 2,(255,255,255),2,cv2.LINE_AA)
        cv2.putText(image,'Jump Gauche',(30,100), font, 1,(255,255,255),2,cv2.LINE_AA)
        cv2.putText(image,'Droite',(355,400), font, 2,(255,255,255),2,cv2.LINE_AA)
        cv2.putText(image,'Jump Droite',(355,100), font, 1,(255,255,255),2,cv2.LINE_AA)


        # afficher l'image
        cv2.imshow('image', image)

        # Deplacer le personnage avec le moteur physique
        self.moteurPhysique.update()

        # Tcheck si on touche un piege sinon on relance direct la Partie
        if arcade.check_for_collision_with_list(self.personnage, self.listePieges):
            self.setup()
            arcade.set_viewport(self.vueGauche, largeurFenetre + self.vueGauche, self.vueBas, hauteurFenetre + self.vueBas)

        # Si le joueur tombe il respawn 
        if self.personnage.bottom < -300:
        	self.setup()
        	arcade.set_viewport(self.vueGauche, largeurFenetre + self.vueGauche, self.vueBas, hauteurFenetre + self.vueBas)

        # Tcheck si on touche le coffre pour afficher la victoire
        if arcade.check_for_collision_with_list(self.personnage, self.listeCoffres):
            view = VictoireView()
            self.window.show_view(view)

        # déplacer le joueur 
        self.listePersonnage.update()

        # update les animations du personnage
        self.listePersonnage.update_animation()

        ###Gestion de la camera ###
        # Vérifier si on doit changer la camera

        change = False

        # defilement de la cam vers la gauche
        if self.personnage.left > 100:
        	limiteGauche = self.vueGauche + 250
        else:
        	limiteGauche = self.vueGauche + 0

        if self.personnage.left < limiteGauche:
        	if self.personnage.left > 250:
        		self.vueGauche -= limiteGauche - self.personnage.left
        		change = True

        # faire defiler la cam vers la droite
        limiteDroite = self.vueGauche + largeurFenetre - margeFenetreDroite
        if self.personnage.right > limiteDroite:
            self.vueGauche += self.personnage.right - limiteDroite
            change = True

        # faire defiler la cam vers le haut
        limiteHaut = self.vueBas + hauteurFenetre - margeFenetreHaut
        if self.personnage.top > limiteHaut:
            self.vueBas += self.personnage.top - limiteHaut
            change = True

        # défiler la cam vers le bas
        limiteBas = self.vueBas + margeFenetreBas
        if self.personnage.bottom < limiteBas:
        	if self.personnage.bottom > 0:
        		self.vueBas -= limiteBas - self.personnage.bottom
        		change = True

        if change:
            # faire défiler que les entiers sinon on se retrouve avec des pixels qui ne sont pas alignés à l'écran.
            self.vueBas = int(self.vueBas)
            self.vueGauche = int(self.vueGauche)

            # Faire le défilement 
            arcade.set_viewport(self.vueGauche,largeurFenetre + self.vueGauche, self.vueBas, hauteurFenetre + self.vueBas)



def main():
    window = arcade.Window(largeurFenetre, hauteurFenetre, titreFenetre)
    startView = JeuView()
    window.show_view(startView)
    startView.setup()
    arcade.run()


main()
