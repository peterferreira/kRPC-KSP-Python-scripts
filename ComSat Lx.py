# -*- coding:utf-8 -*-
#!/usr/bin/python3

# Importar módulos necessários
import math
from time import sleep
import krpc

# Definição de parâmetros do lançamento em metros
iniciar_inclinacao = 100.0
finalizar_inclinacao = 80000.0
altitude_alvo = 716000.0

# Cria conexão com o servidor dentro do KSP e define a nave
conn = krpc.connect(name='ComSat Lx')
vessel = conn.space_center.active_vessel

# Definições para telemetria
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoastro = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
recursos_estagio_1 = vessel.resources_in_decouple_stage(stage=1, cumulative=False)
combustivel1 = conn.add_stream(recursos_estagio_1.amount, 'LiquidFuel')

def plano():
    # Plano para circularizar órbita
    mu = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.apoapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu*((2./r)-(1./a1)))
    v2 = math.sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1
    node = vessel.control.add_node(ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)
    return (node, delta_v)

def calcula_tempo_queima(delta_v):
    f = vessel.available_thrust
    isp = vessel.specific_impulse * 9.82
    m0 = vessel.mass
    m1 = m0 / math.exp(delta_v/isp)
    flow_rate = f / isp
    burn_time = (m0 - m1) / flow_rate
    return burn_time

def orientar(noh):
    escrever('Orient. Manobra')
    vessel.auto_pilot.reference_frame = noh.reference_frame
    vessel.auto_pilot.target_direction = (0, 1, 0)
    vessel.auto_pilot.wait()

def acelerar_tempo_para_queima(burn_time):
    escrever('Acelerando o tempo')
    burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time/2.)
    lead_time = 5
    conn.space_center.warp_to(burn_ut - lead_time)

def abertura():
    # Abrir antenas e paineis solares
    for antenna in vessel.parts.antennas:
        if antenna.deployable:
            escrever('Abrindo antenas')
            antenna.deployed = True
            sleep(0.2)
            escrever('')
    for painelsolar in vessel.parts.solar_panels:
        if painelsolar.deployable:
            escrever('paineis solares')
            painelsolar.deployed = True
            sleep(0.2)
            escrever('')

tela = conn.ui.stock_canvas
tamanho_tela = tela.rect_transform.size
painel = tela.add_panel()
rect = painel.rect_transform
rect.size = (rect.size[0] * 5, rect.size[1])
texto = painel.add_text('Aceleração Máxima')
texto.rect_transform.position = (0, -20)
texto.color = (1, 1, 1)
texto.size = 10
rect.position = (110 - (tamanho_tela[0]/4),0)
def escrever(text):
    texto.content = text
    texto.rect_transform.position = (0, -20)
    texto.color = (1, 1, 1)
    texto.size = 10
    rect.position = (110 - (tamanho_tela[0]/4),0)

# Check in
vessel.control.sas = False
vessel.control.rcs = False
vessel.control.throttle = 1.0
sleep(1)

# Contagem regressiva
escrever('Contagem regressiva')
for n in range(10, 0, -1):
    escrever(str(n))
    sleep(1)

# Ativar primeiro estágio
escrever("Lançamento...")
vessel.control.activate_next_stage()
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90,90)
sleep(1)

# Bora mano!!!
primeiro_estagio_separado = False
segundo_estagio_separado = False
coifa_separada = False
angulo = 0.0
escrever('Giro gravitacional...')
while altitude_alvo >= apoastro():
    # Giro gravitacional
    if altitude() > iniciar_inclinacao and altitude() < finalizar_inclinacao:
        frac = ((altitude() - iniciar_inclinacao) / (finalizar_inclinacao - iniciar_inclinacao))
        novo_angulo = frac * 90
        if abs(novo_angulo - angulo) > 0.5:
            angulo = novo_angulo
            vessel.auto_pilot.target_pitch_and_heading(90-angulo, 90)
            escrever('')

    # Reduzir potência
    if altitude() < 65000:
        if vessel.flight().g_force > 3. and altitude() < 20000:
            vessel.control.throttle = vessel.control.throttle - 0.001
        elif vessel.flight().g_force < 1.1 and altitude() < 20000:
            vessel.control.throttle = vessel.control.throttle + 0.001
    else:
        vessel.control.throttle = 1.0
    
    # Separar primeiro e segundo estágio quando acabar o combustível
    if primeiro_estagio_separado == False:
        if combustivel1() == 0.0:
            if altitude() > 69000:
                escrever('Separação 1º s')
                vessel.control.activate_next_stage()
                sleep(5)
                escrever('Montor 2º s')
                vessel.control.activate_next_stage()
                sleep(3)
                escrever('')
                primeiro_estagio_separado = True

    if coifa_separada == False:
        if altitude() > 65000:
            escrever('Abertura coifa')
            vessel.control.throttle = 0.05
            vessel.control.activate_next_stage()
            sleep(2)
            vessel.control.throttle = 1.0
            coifa_separada = True
            texto.content = ''
    
    # Reduzir aceleração ao se aproximar da altitude alvo
    if apoastro() > altitude_alvo * 0.99:
        vessel.control.throttle = 0.05
        escrever('Ajuste fino')

# Desligar motor

vessel.control.throttle = 0.0
escrever('Desligar motor')
sleep(2)
abertura()

manobra = plano()

tempo_queima = calcula_tempo_queima(manobra[1])

orientar(manobra[0])

acelerar_tempo_para_queima(tempo_queima)

# Executar queima
time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
while time_to_apoapsis() - (tempo_queima/2.) > 0.1:
    pass
escrever('Circ Órbita')
vessel.control.throttle = 1.0
sleep(tempo_queima - 0.1)
escrever('Ajuste fino')
vessel.control.throttle = 0.03
remaining_burn = conn.add_stream(manobra[0].remaining_burn_vector, manobra[0].reference_frame)
while remaining_burn()[1] > 0.05:
    pass
escrever('Completo')
vessel.control.throttle = 0.0
vessel.parts.engines[0].active = False
manobra[0].remove()
vessel.auto_pilot.target_roll = 90
print('Missão cumprida')
sleep(15)
painel.remove()
vessel.auto_pilot.disengage()
conn.close()
