# -*- coding:utf-8 -*-
#!/usr/bin/python3

##################################################################
## Peter Ferreira
## 03/11/2017
## Queria enviar outro projeto, mas não consegui ainda
##################################################################

from time import sleep
import winsound
import math
try:
    import krpc
except:
    import os
    os.system('pip install krpc')
    del(os)
    import krpc

# Definição de parâmetros do lançamento em metros
iniciar_inclinacao = 3000.0
finalizar_inclinacao = 55000.0
altitude_alvo = 2863330.0


# Cria conexão com o servidor dentro do KSP e define a nave
conn = krpc.connect(name='PesteStreamSat e Mantis')
ksc = conn.space_center
nave = ksc.active_vessel
rf = nave.orbit.body.reference_frame

# Definições para telemetria
ut = conn.add_stream(getattr, ksc, 'ut')
altitude = conn.add_stream(getattr, nave.flight(rf), 'mean_altitude')
apoastro = conn.add_stream(getattr, nave.orbit, 'apoapsis_altitude')
recursos_estagio_1 = nave.resources_in_decouple_stage(stage=2, cumulative=False)
combustivel1 = conn.add_stream(recursos_estagio_1.amount, 'LiquidFuel')
recursos_estagio_2 = nave.resources_in_decouple_stage(stage=0, cumulative=False)
combustivel2 = conn.add_stream(recursos_estagio_2.amount, 'LiquidFuel')
altitude_nivel_mar = conn.add_stream(getattr, nave.flight(rf), 'mean_altitude')
velocidade = conn.add_stream(getattr, nave.flight(rf), 'speed')
velocidade_horizontal = conn.add_stream(getattr, nave.flight(rf), 'horizontal_speed')
velocidade_vertical = conn.add_stream(getattr, nave.flight(rf), 'vertical_speed')
impulso = conn.add_stream(getattr, nave, 'max_thrust')
massatotal = conn.add_stream(getattr, nave, 'mass')
massaseca = conn.add_stream(getattr, nave, 'dry_mass')

def calcula_gravidade(AltitudeNave, nave):
    parametro_gravitacional = nave.orbit.body.gravitational_parameter
    RaioAstro = nave.orbit.body.equatorial_radius
    R = RaioAstro + AltitudeNave()
    g = parametro_gravitacional / (R ** 2.)
    return -g

def plano(nave):
    # Plano para circularizar órbita
    mu = nave.orbit.body.gravitational_parameter
    r = nave.orbit.apoapsis
    a1 = nave.orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu*((2./r)-(1./a1)))
    v2 = math.sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1
    node = nave.control.add_node(ut() + nave.orbit.time_to_apoapsis, prograde=delta_v)
    return (node, delta_v)

def calcula_tempo_queima(nave, delta_v):
    f = nave.available_thrust
    isp = nave.specific_impulse * 9.82
    m0 = nave.mass
    m1 = m0 / math.exp(delta_v/isp)
    flow_rate = f / isp
    burn_time = (m0 - m1) / flow_rate
    return burn_time

def orientar(nave, noh):
    t.mensagem('Orient. Manobra')
    nave.auto_pilot.sas = False
    nave.auto_pilot.reference_frame = noh.reference_frame
    nave.auto_pilot.target_direction = (0, 1, 0)
    nave.auto_pilot.wait()

def acelerar_tempo_para_queima(nave, burn_time):
    t.mensagem('Acelerando o tempo')
    burn_ut = ut() + nave.orbit.time_to_apoapsis - (burn_time/2.)
    lead_time = 5
    conn.space_center.warp_to(burn_ut - lead_time)

def abertura(nave):
    # Abrir antenas e paineis solares
    for antenna in nave.parts.antennas:
        if antenna.deployable:
            t.mensagem('Abrindo antenas')
            antenna.deployed = True
            sleep(1)
            t.mensagem('')
    for painelsolar in nave.parts.solar_panels:
        if painelsolar.deployable:
            t.mensagem('Abrindo paineis solares')
            painelsolar.deployed = True
            sleep(1)
            t.mensagem('')

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
        self.rect.size = (self.rect.size[0] * 20, self.rect.size[1])
        self.texto = self.painel.add_text('')
        self.texto.rect_transform.position = (0, -20)
        self.texto.color = (1, 1, 1)
        self.texto.size = 14
        self.rect.position = (110 - (self.tamanho_tela[0] / 8), 0)

    def mensagem(self, text):
        try:
            self.texto.content = text
        except Exception as erro:
            print('Erro: %s' % erro)

def queimar(nave, conn, manobra, tempo_queima, direcao):
    try:
        global t
    except:
        pass
    if direcao == 'prograde':
        while nave.orbit.time_to_apoapsis - (tempo_queima/2.) >= 0.5:
             pass
    elif direcao == 'retrograde':
        while nave.orbit.time_to_periapsis - (tempo_queima/2.) <= -0.5:
            pass

    try:
        t.mensagem('Acelerar 100%')
    except:
        pass
    nave.control.throttle = 1.0
    if direcao == 'prograde':
        sleep(tempo_queima - 0.5)
    else:
        sleep((-1 * tempo_queima) - 0.5)
    try:
        t.mensagem('Ajuste fino')
    except:
        pass
    nave.control.throttle = 0.05
    remaining_burn = conn.add_stream(manobra[0].remaining_burn_vector, manobra[0].reference_frame)
    while remaining_burn()[1] > 0.5:
        pass
    nave.control.throttle = 0.01
    while remaining_burn()[1] > 0.005:
        pass
    nave.control.throttle = 0.0
    del(remaining_burn)

def ControleForcaG(nave):
    # Evita acelerar demais
    global altitude, rf
    if altitude() < 60000:
        if nave.flight(rf).g_force > 2.5:
            nave.control.throttle -= 0.001
        elif nave.flight(rf).g_force < 0.5:
            nave.control.throttle += 0.001
    else:
        nave.control.throttle = 1.0

def contagem_regressiva(som):
    t.mensagem('Contagem regressiva')
    sleep(1)
    som.PlaySound('10-0_countdown.wav', som.SND_FILENAME | som.SND_ASYNC)
    for n in range(10, 0, -1):
        t.mensagem(str(n))
        sleep(0.99)
    t.mensagem('VAI FILHÃO!')
    try:
        del(som)
    except:
        pass

Mantis = None
PesteStreamSat = None
def acencao(nave, altitude_alvo):
    global altitude, iniciar_inclinacao, finalizar_inclinacao, t, Mantis, PesteStreamSat
    # Bora mano!!!
    primeiro_estagio_separado = False
    segundo_estagio_separado = False
    coifa_separada = False
    angulo = 0.0
    while altitude_alvo >= apoastro():
        # Giro gravitacional
        if altitude() > iniciar_inclinacao - 200 and altitude() < iniciar_inclinacao:
            t.mensagem('Iniciando giro gravitacional...')
        if altitude() > iniciar_inclinacao and altitude() < finalizar_inclinacao:
            frac = ((altitude() - iniciar_inclinacao) / (finalizar_inclinacao - iniciar_inclinacao))
            novo_angulo = frac * 90
            if abs(novo_angulo - angulo) > 0.5:
                angulo = novo_angulo
                nave.auto_pilot.target_pitch_and_heading(90-angulo, 90)
                t.mensagem('Inclinando')

        # Reduzir potência para a força G não aloprar
        if altitude() < 70000:
            if altitude() < 60000:
                if nave.flight().g_force > 2.:
                    nave.control.throttle = nave.control.throttle - 0.001
                elif nave.flight().g_force < 1.9:
                    nave.control.throttle = nave.control.throttle + 0.001
            else:
                nave.control.throttle = 1.0

        # Separar primeiro e segundo estágio quando acabar o combustível
        if primeiro_estagio_separado == False:
            if combustivel1() <= 1400.0:
                t.mensagem('Separação 1º s')
                nave.control.throttle = 0.0
                sleep(1)
                nave.control.activate_next_stage()
                nave.control.throttle = 0.1
                nave.auto_pilot.disengage()
                nave.auto_pilot.sas = True
                sleep(1)
                nave.auto_pilot.sas_mode = ksc.SASMode.prograde
                t.mensagem('')
                primeiro_estagio_separado = True
                for vess in ksc.vessels:
                    if vess.name == 'PesteStreamSat Probe':
                        Mantis = vess
                t.mensagem('Apontando para o Prograde')
                sleep(3)
                t.mensagem('Para o 2º estágio reentrar')
                sleep(3)
                t.mensagem('')

        if segundo_estagio_separado == False:
            if combustivel2() == 0.0:
                t.mensagem('Separação 2º s')
                nave.control.activate_next_stage()
                PesteStreamSat = ksc.active_vessel
                t.mensagem('')
                segundo_estagio_separado = True
                abertura(nave)
        if primeiro_estagio_separado == True:
            if coifa_separada == False:
                if altitude() > 69000:
                    t.mensagem('Liberando coifa protetora')
                    nave.control.throttle = 0.1
                    nave.control.activate_next_stage()
                    sleep(3)
                    nave.control.throttle = 1.0
                    coifa_separada = True
        ControleForcaG(nave)

        # Reduzir aceleração ao se aproximar da altitude alvo
        if apoastro() > altitude_alvo * 0.98:
            nave.control.throttle = 0.005
            t.mensagem('Ajuste fino')
    # Desligar motor
    nave.control.throttle = 0.0
    t.mensagem('Desligar motor')
    # Reativa o auto_pilot
    nave.control.sas = False
    sleep(1)
    nave.auto_pilot.engage()
    sleep(1)
    nave.auto_pilot.target_direction = (0, 1, 0)
    sleep(2)

def lancamento(nave):
    global t
    # Check in
    nave.auto_pilot.sas = False
    nave.auto_pilot.rcs = False
    nave.control.throttle = 1.0
    sleep(1)
    # Ativar primeiro estágio
    t.mensagem("Lançamento...")
    nave.control.activate_next_stage()
    nave.auto_pilot.engage()
    nave.auto_pilot.target_pitch_and_heading(90, 90)
    sleep(1)
    t.mensagem('')

def circular_orbita(nave):
    manobra = plano(nave)
    tempo_queima = calcula_tempo_queima(nave, manobra[1])
    orientar(nave, manobra[0])
    sleep(2)
    acelerar_tempo_para_queima(nave, tempo_queima)
    # Executar queima
    queimar(nave, conn, manobra, tempo_queima, 'prograde')
    
def voltar(nave):
    global Mantis, t
    t.mensagem('Retorno 1º estágio')
    sleep(3)
    t.mensagem('Virando para o retrograde')
    ksc.active_vessel = Mantis
    nave = ksc.active_vessel
    nave.name = 'Mantis'
    nave.control.throttle = 0.0
    nave.control.rcs = True
    nave.control.sas = True
    sleep(2)
    nave.auto_pilot.sas_mode = ksc.SASMode.retrograde

def pousar(nave):
    global t, Mantis
    del(t)
    t = tela()
    nave.auto_pilot.sas = True
    nave.auto_pilot.rcs = True
    try:
        nave.auto_pilot.sas_mode = ksc.SASMode.retrograde
    except:
        pass

    altitude_mantis = conn.add_stream(getattr, nave.flight(rf), 'surface_altitude')
    velocidade_mantis = conn.add_stream(getattr, nave.flight(rf), 'speed')
    velocidade_vertical_mantis = conn.add_stream(getattr, nave.flight(rf), 'vertical_speed')
    impulso_mantis = conn.add_stream(getattr, nave, 'max_thrust')
    massatotal_mantis = conn.add_stream(getattr, nave, 'mass')

    while not nave.parts.legs[0].is_grounded:
        if altitude_mantis() < 5000:
            ControlePouso(nave, velocidade_vertical_mantis, velocidade_mantis, altitude_mantis, massatotal_mantis, impulso_mantis, True)
        if not nave.control.brakes:
            if altitude_mantis() < 50000:
                nave.control.brakes = True
                t.mensagem('Ligando os aerofreios')
        if not nave.control.gear:
            if velocidade_vertical_mantis() > -100 and altitude_mantis() < 500:
                nave.control.gear = True
                t.mensagem('Baixando as pernas')

    nave.control.throttle = 0.0
    nave.control.brakes = False
    nave.auto_pilot.sas = True
    nave.auto_pilot.sas_mode = ksc.SASMode.radial
    t.mensagem('')
    del(t)

def ControlePouso(nave, velocidade_vertical, velocidade, altitude, massatotal, impulso, atmosfera = True):
    if velocidade() > 50:
        if altitude() <= (calcula_queima_suicida(velocidade, impulso, massatotal, altitude, nave) - velocidade()):
            nave.control.throttle = 1.0
            t.mensagem('Motor ligado')
    else:
        gravidade = calcula_gravidade(altitude, nave)
        try:
            zeraraceleracao = (massatotal() * -gravidade) / impulso()
        except:
            zeraraceleracao = nave.control.throttle
        if atmosfera:
            if velocidade() < 100:
                if velocidade_vertical() < -5 and velocidade_vertical() > -8:
                    nave.control.throttle = zeraraceleracao
                elif velocidade_vertical() > -5:
                    nave.control.throttle = zeraraceleracao - 0.1
                elif velocidade_vertical() < -8:
                    nave.control.throttle = zeraraceleracao + 0.1
            t.mensagem('Lentamente...')
        else:
            if altitude() > 90 and altitude() < 50:
                if velocidade_vertical() < -9 and velocidade_vertical() > -10:
                    nave.control.throttle = zeraraceleracao
                elif velocidade_vertical() > -9:
                    nave.control.throttle = zeraraceleracao - 0.1
                elif velocidade_vertical() < -10:
                    nave.control.throttle = zeraraceleracao + 0.1
            elif altitude() > 30 and altitude() < 90:
                if velocidade_vertical() < -5 and velocidade_vertical() > -6:
                    nave.control.throttle = zeraraceleracao
                elif velocidade_vertical() > -5:
                    nave.control.throttle = zeraraceleracao - 0.1
                elif velocidade_vertical() < -6:
                    nave.control.throttle = zeraraceleracao + 0.1
            elif altitude() > 15 and altitude() < 30:
                if velocidade_vertical() < -1 and velocidade_vertical() > -3:
                    nave.control.throttle = zeraraceleracao
                elif velocidade_vertical() > -1:
                    nave.control.throttle = zeraraceleracao - 0.1
                elif velocidade_vertical() < -3:
                    nave.control.throttle = zeraraceleracao + 0.1
            elif altitude() < 15:
                if velocidade_vertical() < -0.75 and velocidade_vertical() > -1.25:
                    nave.control.throttle = zeraraceleracao
                elif velocidade_vertical() > -0.5:
                    nave.control.throttle = zeraraceleracao - 0.1
                elif velocidade_vertical() < -1.1:
                    nave.control.throttle = zeraraceleracao + 0.1
    try:
        if altitude() > 100.0:
            if nave.control.sas_mode is not ksc.SASMode.retrograde:
                nave.control.sas_mode = ksc.SASMode.retrograde
        else:
            if nave.control.sas_mode is not ksc.SASMode.radial:
                nave.control.rcs = True
                nave.auto_pilot.sas_mode = ksc.SASMode.radial
    except:
        pass

def calcula_queima_suicida(Velocidade, Impulso, Massa, altitude, nave):
    # Tá, é meio roubo, mas não tá 100% perfeito ainda e precisava enviar antes da live.
    margem_de_seguranca = 1.5 #se não está dando tempo de reduzir velocidade, tente entre 1.1 e 1.2
    gravidade = calcula_gravidade(altitude, nave)
    try:
        va = ((Impulso()/Massa()) + gravidade)
        A = (Velocidade() ** 2) / (2 * va)
    except:
        va = 1000.0
        A = 0.5
    return A * margem_de_seguranca

def rendezvous(nave, target):
    # Não consegui terminar essa semana, é difícil demais,
    # vou continuar tentando para as próximas semanas
    pass

def docking(nave, target):
    # Isso é menos difícil, mas como não fiz o rendezvous ainda
    # Insira aqui o arco-íris do Gaveta
    pass

t = tela()
contagem_regressiva(winsound)
lancamento(nave)

PesteStreamSat = nave
acencao(nave, altitude_alvo)
sleep(2)
ksc.active_vessel = Mantis
sleep(5)
voltar(Mantis)
pousar(Mantis)
# Removendo o objeto de tela, por que as vezes o texto fica sobreposto
try:
    del(t)
except:
    pass
t = tela()
t.mensagem('ESTOU PRONTO!!!')
sleep(10)
ksc.active_vessel = PesteStreamSat
sleep(3)
nave = ksc.active_vessel
circular_orbita(nave)
t.mensagem('PesteStreamSat Entregue')
sleep(5)
ksc.active_vessel = Mantis
del(t)
t = tela()
t.mensagem('Missão Cumprida sem R.U.D.')
print('Missão cumprida')
sleep(10)
t.mensagem('Deixe o seu like!')
sleep(4)
t.mensagem('Assista até o final!')
sleep(4)
t.mensagem('Compartilhe com os amigos')
sleep(4)
t.mensagem('Se inscreva no canal!')
sleep(5)
nave.control.rcs = False
conn.close()

