# -*- coding:utf-8 -*-
#!/usr/bin/python3

# Autor: Peter Ferreira <peterkid@gmail.com>
# Data Inicio: 15/10/2017
# Ultima atualização: 21/10/2017

# Importar módulos necessários
import math
from time import sleep
import krpc
import winsound

# Definição de parâmetros do lançamento em metros
iniciar_inclinacao = 500.0
finalizar_inclinacao = 45000.0
altitude_alvo = 4363334.0
altitude_sincronia = 2863500.0 #aproximadamente 2h
altitude_retorno = 37000.0

# Cria conexão com o servidor dentro do KSP e define a nave
conn = krpc.connect(name='Lançamento #Pestestream!')
ksp = conn.space_center
navemae = ksp.active_vessel
vessel = navemae

# Definições para telemetria
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoastro = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
periastro = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
recursos_estagio_1 = vessel.resources_in_decouple_stage(stage=8, cumulative=False)
combustivel1 = conn.add_stream(recursos_estagio_1.amount, 'LiquidFuel')
recursos_estagio_2 = vessel.resources_in_decouple_stage(stage=9, cumulative=False)
combustivel2 = conn.add_stream(recursos_estagio_2.amount, 'SolidFuel')
altitude_sincronia += vessel.orbit.body.equatorial_radius

def AnguloAtaque(vessel):
    d = vessel.direction(vessel.orbit.body.reference_frame)
    v = vessel.velocity(vessel.orbit.body.reference_frame)

    # Compute the dot product of d and v
    dotprod = d[0]*v[0] + d[1]*v[1] + d[2]*v[2]

    # Compute the magnitude of v
    vmag = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    # Note: don't need to magnitude of d as it is a unit vector

    # Compute the angle between the vectors
    angle = 0
    if dotprod > 0:
        angle = abs(math.acos(dotprod / vmag) * (180.0 / math.pi))
    return angle


def circular_retrograde(vessel):
    # circular_retrograde para circularizar órbita
    mu = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.periapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu*((2./r)-(1./a1)))
    v2 = math.sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1
    node = vessel.control.add_node(ut() + vessel.orbit.time_to_periapsis, prograde=delta_v)
    return (node, delta_v)

def circular_prograde(vessel):
    # circular_prograde para circularizar órbita
    mu = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.apoapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu*((2./r)-(1./a1)))
    v2 = math.sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1
    node = vessel.control.add_node(ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)
    return (node, delta_v)

def sincronia(altitude_sincronia, vessel):
    # circular_retrograde para órbita de sincronia
    GM = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.apoapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = altitude_sincronia + vessel.orbit.body.equatorial_radius * math.pi + vessel.orbit.periapsis
    v1 = math.sqrt(GM*((2./r)-(1./a1)))
    v2 = math.sqrt(GM*((2./r)-(1./a2)))
    delta_v = 353.83 # F*d@ c não achei o calculo, fiz a manobra na mão e colei aqui. Depois aprendo a equação certa. Não ia dar tempo ate a #Pestestream
    node = vessel.control.add_node(ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)
    return (node, delta_v)

def calcula_tempo_queima(delta_v, vessel):
    f = vessel.available_thrust
    isp = vessel.specific_impulse * 9.82
    m0 = vessel.mass
    m1 = m0 / math.exp(delta_v/isp)
    flow_rate = f / isp
    burn_time = (m0 - m1) / flow_rate
    return burn_time

def orientar(noh, vessel):
    vessel.auto_pilot.reference_frame = noh.reference_frame
    vessel.auto_pilot.target_direction = (0, 1, 0)
    t.mensagem('Orient. Manobra')
    vessel.auto_pilot.wait()

def acelerar_tempo_para_apoastro_queima(burn_time, vessel):
    burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time/2.)
    lead_time = 5
    t.mensagem('Acel. tempo')
    conn.space_center.warp_to(burn_ut - lead_time)
    t.mensagem('')

def acelerar_tempo_para_periastro_queima(burn_time, vessel):
    burn_ut = ut() + vessel.orbit.time_to_periapsis - (burn_time/2.)
    lead_time = 10
    t.mensagem('Acel. tempo')
    conn.space_center.warp_to(burn_ut - lead_time)
    t.mensagem('')

def abertura(vessel):
    # Abrir antenas e paineis solares
    for painelsolar in vessel.parts.solar_panels:
        if painelsolar.deployable:
            t.mensagem('Abrindo paineis solares')
            painelsolar.deployed = True
            sleep(1)
    for antenna in vessel.parts.antennas:
        if antenna.deployable:
            t.mensagem('Abrindo antenas')
            antenna.deployed = True
            sleep(1)
    t.mensagem('')
            
def queimar(vessel, conn, manobra, tempo_queima, direcao):
    try:
        global t
    except:
        pass
    if direcao == 'apoastro':
        while vessel.orbit.time_to_apoapsis - (tempo_queima/2.) >= 0.5:
             pass
    elif direcao == 'periastro':
        while vessel.orbit.time_to_periapsis - (tempo_queima/2.) <= -0.5:
            pass

    try:
        t.mensagem('Acelerar 100%')
    except:
        pass
    vessel.control.throttle = 1.0
    if direcao == 'apoastro':
        sleep(tempo_queima - 0.5)
    else:
        sleep((-1 * tempo_queima) - 1.0)
    try:
        t.mensagem('Ajuste fino')
    except:
        pass
    vessel.control.throttle = 0.05
    remaining_burn = conn.add_stream(manobra[0].remaining_burn_vector, manobra[0].reference_frame)
    while remaining_burn()[1] > 0.5:
        pass
    vessel.control.throttle = 0.01
    while remaining_burn()[1] > 0.01:
        pass
    vessel.control.throttle = 0.0

def EntregaSatelites(navemae, ksp):
    for n in range(4):
        global t
        t = tela()
        t.mensagem('')
        try:
            vessel.auto_pilot.disengage()
        except:
            pass
        vessel.auto_pilot.sas = True
        vessel.auto_pilot.sas_mode = ksp.SASMode.prograde
        t.mensagem('Apontando p/ prograde')
        sleep(5)
        t.mensagem('Liberando Sat')
        sat = navemae.control.activate_next_stage()
        ksp.active_vessel = sat[0]
        t.mensagem('Renomeando Sat')
        sleep(2)
        sat[0].name = navemae.name + ' ' + str(n+1)
        abertura(ksp.active_vessel)
        t.mensagem('Ativando Motor')
        sat[0].control.throttle = 0.0
        sat[0].parts.engines[0].active = True
        sat[0].auto_pilot.engage()
        sleep(1)
        manobra = circular_retrograde(sat[0])
        tempo_queima = calcula_tempo_queima(manobra[1], sat[0])
        orientar(manobra[0], sat[0])
        sleep(3)
        acelerar_tempo_para_periastro_queima(tempo_queima, sat[0])
        queimar(sat[0], conn, manobra, tempo_queima, 'periastro')
        t.mensagem('Remover Manobra')
        sleep(1)
        manobra[0].remove()
        t.mensagem('Desativar Motor')
        sleep(1)
        sat[0].parts.engines[0].active = False
        del(sat[0])
        t.mensagem('Ir p/ Nave Mãe')
        sleep(1)
        t.mensagem('')
        del(t)
        vessel.auto_pilot.disengage()
        ksp.active_vessel = navemae
        sleep(10)

class tela():
    quadro = None
    tamanho_tela = None
    peinel = None
    retangulo = None
    texto = None
    def __init__(self):
        self.quadro = conn.ui.stock_canvas
        self.tamanho_tela = self.quadro.rect_transform.size
        self.painel = self.quadro.add_panel()
        self.rect = self.painel.rect_transform
        self.rect.size = (self.rect.size[0] * 10, self.rect.size[1])
        self.texto = self.painel.add_text('')
    
    def mensagem(self, text):
        try:
            self.texto.content = text
            self.texto.rect_transform.position = (0, -20)
            self.texto.color = (1, 1, 1)
            self.texto.size = 14
            self.rect.position = (110 - (self.tamanho_tela[0]/4),0)
        except Exception as erro:
            print('Erro: %s' % erro)

def ControleForcaG(vessel):
    # Evita acelerar demais
    global altitude
    if altitude() < 60000:
        if vessel.flight().g_force > 2.5:
            vessel.control.throttle -= 0.01
        elif vessel.flight().g_force < 0.5:
            vessel.control.throttle += 0.01
        else:
            vessel.control.throttle = 1.0

def ControlePouso(vessel):
    if vessel.flight(vessel.orbit.body.reference_frame).bedrock_altitude < 100:
        if vessel.flight(vessel.orbit.body.reference_frame).vertical_speed > -3.0:
            vessel.control.throttle -= 0.01
            t.mensagem('Menos aceleração')
        elif vessel.flight(vessel.orbit.body.reference_frame).vertical_speed <= -6.0:
            vessel.control.throttle += 0.01
            t.mensagem('Mais aceleração')
            
# Check in
vessel.control.sas = False
vessel.control.rcs = False
vessel.control.throttle = 1.0
sleep(1)
t = tela()

# Contagem regressiva
t.mensagem('Contagem regressiva')
sleep(1)
try:
    winsound.PlaySound('10-0_countdown.wav', winsound.SND_FILENAME)
except:
    pass

for n in range(10, 0, -1):
    t.mensagem(str(n))
    sleep(0.98)

try:
    del(contagem)
    del(simpleaudio)
except:
    pass

# Ativar primeiro estágio
t.mensagem("Lançamento...")
vessel.control.activate_next_stage()
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90,90)
sleep(1)

# Bora mano!!!
primeiro_estagio_separado = False
segundo_estagio_separado = False
coifa_separada = False
angulo = 0.0
while altitude_alvo >= apoastro():
    # Giro gravitacional
    t.mensagem('')
    if altitude() > iniciar_inclinacao and altitude() < finalizar_inclinacao:
        frac = ((altitude() - iniciar_inclinacao) / (finalizar_inclinacao - iniciar_inclinacao))
        novo_angulo = frac * 90
        if abs(novo_angulo - angulo) > 0.5:
            t.mensagem("Inclinando...")
            sleep(0.3)
            angulo = novo_angulo
            vessel.auto_pilot.target_pitch_and_heading(90-angulo, 90)

    ControleForcaG(vessel)
    
    # Separar primeiro e segundo estágio quando acabar o combustível
    if primeiro_estagio_separado == False:
        if combustivel2() == 0.0:
            t.mensagem('Separação 1º s')
            vessel.control.activate_next_stage()
            sleep(0.5)
            primeiro_estagio_separado = True
    if segundo_estagio_separado == False:
        if combustivel1() == 0.0:
            t.mensagem('Separação 2º s')
            vessel.control.activate_next_stage()
            for contagem in range(20, 0, -1):
                t.mensagem('Ligar motor em %ds' % contagem)
                sleep(1)
            vessel.control.activate_next_stage()
            segundo_estagio_separado = True
    if coifa_separada == False:
        if altitude() > 60000:
            t.mensagem('Abertura coifa')
            vessel.control.throttle = 0.05
            sleep(1)
            vessel.control.activate_next_stage()
            sleep(2)
            vessel.control.throttle = 1.0
            coifa_separada = True
            t.mensagem('')
    
    # Reduzir aceleração ao se aproximar da altitude alvo
    if apoastro() > altitude_alvo * 0.97 and apoastro() < altitude_alvo * 0.99:
        vessel.control.throttle = 0.05
        t.mensagem('Ajuste fino')
    elif apoastro() > altitude_alvo * 0.9999:
        vessel.control.throttle = 0.01
        t.mensagem('Ajuste fino')

# Desligar motor
vessel.control.throttle = 0.0
t.mensagem('Acel. Zero')
sleep(2)

manobra = sincronia(altitude_sincronia, vessel)

tempo_queima = calcula_tempo_queima(manobra[1], vessel)

orientar(manobra[0], vessel)
sleep(6)
acelerar_tempo_para_apoastro_queima(tempo_queima, vessel)

# Executar queima
queimar(vessel, conn, manobra, tempo_queima, 'apoastro')
t.mensagem('Removendo manobra')
manobra[0].remove()
sleep(1)
t.mensagem('')
del(t)
EntregaSatelites(vessel, ksp)
t = tela()
# Retornar para a atmosfera
t.mensagem('Retornando...')
sleep(2)
t.mensagem('Retrograde')
vessel = ksp.active_vessel 
vessel.auto_pilot.reference_frame = vessel.orbital_reference_frame
vessel.auto_pilot.sas = True
vessel.auto_pilot.sas_mode = ksp.SASMode.retrograde
sleep(5)
vessel.control.throttle = 1.0
while vessel.orbit.periapsis_altitude > 100000:
    pass
t.mensagem('Suave')
vessel.control.throttle = 0.1
while vessel.orbit.periapsis_altitude > altitude_retorno:
    pass
t.mensagem('Aprendendo com Peste!')
vessel.control.throttle = 0.0
vessel.auto_pilot.sas_mode = ksp.SASMode.prograde
sleep(1)
vessel.control.activate_next_stage()
sleep(1)
vessel.control.activate_next_stage()
ksp.warp_to(ut()+vessel.orbit.time_to_periapsis - 120)
vessel.auto_pilot.sas_mode = ksp.SASMode.retrograde

pousou = False
while not pousou:
    if vessel.flight(vessel.orbit.body.reference_frame).bedrock_altitude >= 3.:
        ControlePouso(vessel)
    else:
        pousou = True
        
vessel.control.throttle = 0.0
vessel.auto_pilot.sas_mode = ksp.SASMode.radial
t.mensagem('Missão cumprida')
print('Missão cumprida')
sleep(5)
t.mensagem('#PESTESTREAM!')
sleep(5)
t.painel.remove()
del(t)
vessel.recover()
conn.close()
