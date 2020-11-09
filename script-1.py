import random
import threading
import time
import logging

logging.basicConfig(format='%(asctime)s.%(msecs)03d [%(threadName)s] - %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

latasDeSobra = 0  #Variable global para guardar las latas sobrantes
botellasDeSobra = 0 #Variable global para guardar las botellas sobrantes
numeroHeladera = 0 #para el ínidce de las heladeras

semaforoProveedor = threading.Semaphore(1) #semaforo para que haya de a un proveedor
semaforoDeLatas = threading.Semaphore(1)
semaforoDeBotellas = threading.Semaphore(1)
semaforoLataPinchada = threading.Semaphore(1)
cantidadDeHeladeras = 5
cantidadDeProveedores = 30

class Heladera():
    def __init__(self, numero):  
        super().__init__()
        self.name = f'Heladera {numero}'
        self.cantidadDeLatas = []
        self.cantidadDeBotellas = [] 
        self.filaDeBeodes = []
        
    
    def latasEnHeladera(self):
        return len(self.cantidadDeLatas)

    def botellasEnHeladera(self):
        return len(self.cantidadDeBotellas)

    def estaLlena(self):
        return self.latasEnHeladera()==15 and self.botellasEnHeladera()==10
    
    def estaVacia(self):
        return self.latasEnHeladera()==0 and self.botellasEnHeladera()==0
    
    def cantidadesEnHeladera(self):
        print('En la heladera hay => Latas: '+ str(len(self.cantidadDeLatas))+' y Botellas: '+ str(len(self.cantidadDeBotellas)))
    
def lataPinchada():
    global heladeras
    while True:
        semaforoLataPinchada.acquire()
        helDeLataPinchada = heladeras[random.randint(0, len(heladeras)-1)]
        time.sleep(random.randint(10,20))
        if(helDeLataPinchada.latasEnHeladera()>0):
            logging.info(f'Hay una lata pinchada en la heladera {helDeLataPinchada.name}, la saco')
            helDeLataPinchada.cantidadDeLatas.pop(0)
        semaforoLataPinchada.release()


class Proveedor(threading.Thread):  #cada proveedor tiene un número y una cantidad random de latas y botellas
    def __init__(self, numero, monitorLata, monitorBotella):
        super().__init__()
        self.name = f'Proveedor {numero}'
        self.latasAPoner = self.cantidadAReponer()
        self.botellasAPoner = self.cantidadAReponer()
        self.monitorLata = monitorLata
        self.monitorBotella = monitorBotella

    def cantidadAReponer(self):   
        return random.randint(1,10)
        
    def tiempo(self):
        return random.randint(1, 5)

    def cargarLatas(self, heladera, cantidad):   
        global latasDeSobra
        logging.info(f'Cargando {cantidad} latas')
        for i in range(cantidad):
            if (heladera.latasEnHeladera()<15):
                with self.monitorLata:
                    heladera.cantidadDeLatas.append(i)
                    self.monitorLata.notify()
            else:
                latasDeSobra += 1

    def cargarBotellas(self, heladera, cantidad):
        global botellasDeSobra
        logging.info(f'Cargando {cantidad} botellas')
        for i in range(cantidad):
            if (heladera.botellasEnHeladera()<10):
                with self.monitorBotella:
                    heladera.cantidadDeBotellas.append(i)
                    self.monitorBotella.notify()
            else:
                botellasDeSobra += 1
    
    def reponerHeladera(self, heladera):

        global latasDeSobra, botellasDeSobra, numeroHeladera #dejo las botellas y latas de sobra para reponer

        self.latasAPoner = self.latasAPoner + latasDeSobra
        self.botellasAPoner = self.botellasAPoner + botellasDeSobra
        latasDeSobra=0
        botellasDeSobra=0
        if(heladera.estaVacia()):
            logging.info('Enchufo la heladera número '+ str(numeroHeladera))
        
        
        time.sleep(self.tiempo())
        self.cargarLatas(heladera, self.latasAPoner)
        time.sleep(self.tiempo())
        self.cargarBotellas(heladera, self.botellasAPoner)
        if (heladera.estaLlena()):
            heladera.cantidadesEnHeladera()
            print()
            logging.info('Apretando el botón de enfriado rápido de la heladera '+str(numeroHeladera))
            print('Latas Sobrantes: '+ str(latasDeSobra)+' y Botellas: '+ str(botellasDeSobra))
        else: 
            heladera.cantidadesEnHeladera()
        semaforoProveedor.release()
        exit()

    def run(self):
        global heladeras, numeroHeladera
        semaforoProveedor.acquire()
        time.sleep(random.randint(1,5)) #dejo este tiempo para que no esté cargando a cada rato
        logging.info('Latas a poner: '+ str(self.latasAPoner)+' y Botellas: '+ str(self.botellasAPoner))
       
        if(heladeras[numeroHeladera].estaLlena() and numeroHeladera<(len(heladeras)-1)):
            numeroHeladera += 1

        while not(heladeras[numeroHeladera].estaLlena()):
            self.reponerHeladera(heladeras[numeroHeladera])
        logging.info('Las heladeras están llenas')
        semaforoProveedor.release()
        exit()

class Beode(threading.Thread):
    def __init__(self, numero, heladera, monitorLata, monitorBotella):
        super().__init__()
        self.name = f'Beode {numero}'
        self.heladera = heladera
        self.latasABeber = random.randint(3,7) 
        self.botellasABeber = random.randint(1,4)
        self.monitorBotella = monitorBotella
        self.monitorLata = monitorLata

    
    def beberLatas(self):
        #for para que beba la cantidad de latas antes de desmayarse
        for i in range(self.latasABeber):
            with self.monitorLata:
                while self.heladera.latasEnHeladera()==0:
                    self.monitorLata.wait()
                logging.info(f'Tomando la latita..')
                self.heladera.cantidadDeLatas.pop(0)
        logging.info(f'Llegué a mi límite de latas, me demayo....')
        semaforoDeLatas.release()
        exit()

    def beberBotellas(self):
        for i in range(self.botellasABeber):
            with self.monitorBotella:
                while self.heladera.botellasEnHeladera()==0:
                    self.monitorBotella.wait()
                logging.info(f'Tomando la botella..')
                self.heladera.cantidadDeBotellas.pop(0)
        logging.info(f'Llegué a mi límite de botellas, me demayo....')
        semaforoDeBotellas.release()
        exit()

    def beodeEmpedernido(self):

        for i in range(self.botellasABeber):
            with self.monitorBotella:
                while self.heladera.botellasEnHeladera()==0:
                    self.monitorBotella.wait()
                logging.info(f'Tomando la botella..')
                self.heladera.cantidadDeBotellas.pop(0)
                semaforoDeBotellas.release()
        logging.info(f'Llegué a mi límite de botellas, todaviiiia me quednnnn llas laaataaass....')
        for i in range(self.latasABeber):
            with self.monitorLata:
                while self.heladera.latasEnHeladera()==0:
                    self.monitorLata.wait()
                logging.info(f'Tomando la latita..')
                self.heladera.cantidadDeLatas.pop(0)
        logging.info(f'Llegué a mi límite total, me demayo....')
        semaforoDeLatas.release()
        exit()
    

    
    
    def run(self):
        caso = random.choice([0,1,2]) #aleatoriamente saco o pongo
        if(caso == 0):
            logging.info(f'Hola soy un beode de latas, me toca la heladera {self.heladera.name} ')
            semaforoDeLatas.acquire()
            self.beberLatas()
        if(caso == 1):
            logging.info(f'Hola soy un beode de botellas, me toca la heladera {self.heladera.name} ')
            semaforoDeBotellas.acquire()
            self.beberBotellas()
        if(caso == 2):
            logging.info(f'Hola soy un beode de latas y botellas, me toca la heladera {self.heladera.name} ')
            semaforoDeBotellas.acquire()
            self.beodeEmpedernido()

heladeras = [] #Lista para guardar las heladeras          
latas = threading.Condition()
botellas = threading.Condition()

for i in range(cantidadDeHeladeras):
    heladeras.append(Heladera(i))
    
    
for i in range(cantidadDeProveedores):
    Proveedor(i,latas,botellas).start()



for i in range(5):
    num = random.randint(0, len(heladeras)-1)
    heladeras[num].filaDeBeodes.append(i)
    Beode(i,heladeras[i],latas,botellas).start()

pincharLata = threading.Thread(target = lataPinchada, name = "Lata Pinchada")
pincharLata.start()