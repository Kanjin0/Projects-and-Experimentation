class Material:
    def __init__(self, name = "default", diffuse = (1.0,1.0,1.0), ambient = None, specular = (1.0,1.0,1.0), shininess = 32., transparency = 1.0):

        self.name = name
        # Colors are stored as (r, g, b) in range 0.0 - 1.0
        self.diffuse = diffuse
        self.ambient = ambient
        self.specular = specular
        self.shininess = shininess
        self.transparency = transparency

    def __repr__(self) -> str:
        return f"Material ({self.name}) Characteristics:\nDiffuse = {self.diffuse}\nAmbient = {self.ambient}\nSpecular = {self.specular}\nShininess = {self.shininess}\n Transparency = {self.transparency}"
    

DEFAULT_MAT = Material(name="default",
    diffuse=(96/255, 47/255, 189/255),  # FACE_COLOR
    specular=(1.0, 1.0, 1.0),
    shininess=32)