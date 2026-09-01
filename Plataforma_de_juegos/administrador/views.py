from django.shortcuts import render
from .models import Juego, PerfilUsuario
from datetime import date

def catalogo_juegos(request):
    # 1. Filtro base: Solo traer juegos que hayan pasado el anti-malware y no estén baneados
    # Equivalente SQL: SELECT * FROM Juego WHERE estado = 'publicado'
    juegos_disponibles = Juego.objects.filter(estado='publicado')

    # 2. Lógica del Diagrama: "Consulta SQL: Omite juegos +18 si es menor o invitado"
    if request.user.is_authenticated:
        try:
            # Buscamos el perfil del usuario logueado
            perfil = request.user.perfilusuario
            
            if perfil.fecha_nacimiento:
                # Calculamos la edad exacta hoy
                hoy = date.today()
                edad = hoy.year - perfil.fecha_nacimiento.year - ((hoy.month, hoy.day) < (perfil.fecha_nacimiento.month, perfil.fecha_nacimiento.day))
                
                # Si es menor de 18, añadimos un filtro extra (Equivalente a: AND etiqueta_mas_18 = False)
                if edad < 18:
                    juegos_disponibles = juegos_disponibles.filter(etiqueta_mas_18=False)
            else:
                # Si el usuario no cargó su fecha de nacimiento, por precaución ocultamos los +18
                juegos_disponibles = juegos_disponibles.filter(etiqueta_mas_18=False)
                
        except PerfilUsuario.DoesNotExist:
            # Si hay un error con el perfil, aplicamos restricción
            juegos_disponibles = juegos_disponibles.filter(etiqueta_mas_18=False)
    else:
        # Si es un usuario "invitado" (no inició sesión), bloqueamos el contenido +18
        juegos_disponibles = juegos_disponibles.filter(etiqueta_mas_18=False)

    # 3. Enviamos el resultado de la consulta al frontend
    contexto = {
        'juegos': juegos_disponibles
    }
    return render(request, 'catalogo.html', contexto)