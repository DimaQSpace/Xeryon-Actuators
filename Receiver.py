# plot.py
import sys
import socket
import numpy as np
import pyqtgraph as pg
from PyQt6 import QtCore, QtWidgets

class LivePhysicsPlot(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        # Настройка UDP сокета
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 5005))
        self.sock.setblocking(False) # Неблокирующий режим, чтобы окно не зависало
        print("График запущен и слушает порт 5005...")
        
        # Настройка окна
        self.setWindowTitle("Анализ динамики пьезопривода через UDP")
        self.resize(1000, 800)
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Сетка графиков PyQtGraph
        self.win = pg.GraphicsLayoutWidget()
        self.layout.addWidget(self.win)
        
        # Размер скользящего окна истории (храним последние 500 принятых точек)
        self.max_points = 500
        self.time_history = np.zeros(self.max_points)
        self.target_history = np.zeros(self.max_points)
        self.real_history = np.zeros(self.max_points)
        
        # --- ГРАФИК 1: ПОЛОЖЕНИЕ ---
        self.p1 = self.win.addPlot(title="Положение штока (ед.)")
        self.p1.addLegend()
        self.p1.showGrid(x=True, y=True, alpha=0.3)
        self.curve_target = self.p1.plot(pen=pg.mkPen('r', width=1, style=QtCore.Qt.PenStyle.DashLine), name="Целевое")
        self.curve_real = self.p1.plot(pen=pg.mkPen('g', width=2), name="Реальное")
        
        self.win.nextRow()
        
        # --- ГРАФИК 2: СКОРОСТЬ ---
        self.p2 = self.win.addPlot(title="Скорость штока (ед/с)")
        self.p2.showGrid(x=True, y=True, alpha=0.3)
        self.curve_velocity = self.p2.plot(pen=pg.mkPen('c', width=1.5))
        
        self.win.nextRow()
        
        # --- ГРАФИК 3: УСКОРЕНИЕ ---
        self.p3 = self.win.addPlot(title="Ускорение штока (ед/с²)")
        self.p3.setLabel('bottom', "Время", units='с')
        self.p3.showGrid(x=True, y=True, alpha=0.3)
        self.curve_acceleration = self.p3.plot(pen=pg.mkPen('m', width=1.5))
        
        # Синхронизация осей X (зум верхнего графика масштабирует нижние)
        self.p2.setXLink(self.p1)
        self.p3.setXLink(self.p1)
        
        # Быстрый таймер для вычитки сети и обновления экрана (каждые 16 мс ~ 60 FPS)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_system)
        self.timer.start(16)

    def update_system(self):
        has_new_data = False
        
        # Выгребаем ВСЕ скопившиеся в сети пакеты, чтобы не было задержек отображения
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                message_str = data.decode('utf-8')
                
                # Парсим строку "Время,Цель,Факт"
                t_val, target_val, real_val = map(float, message_str.split(","))
                
                # Сдвигаем массивы истории влево и вставляем новую точку в конец
                self.time_history[:-1] = self.time_history[1:]
                self.time_history[-1] = t_val
                
                self.target_history[:-1] = self.target_history[1:]
                self.target_history[-1] = target_val
                
                self.real_history[:-1] = self.real_history[1:]
                self.real_history[-1] = real_val
                
                has_new_data = True
            except BlockingIOError:
                # Все новые пакеты из сети прочитаны
                break
            except Exception:
                break
        
        # Если прилетели новые точки — пересчитываем физику и обновляем линии
        if has_new_data:
            # Считаем реальный шаг времени между точками (dt)
            dt_array = np.diff(self.time_history)
            # Защита от деления на ноль, если шаг времени за за кадр не изменился
            dt_array[dt_array == 0] = 0.001 
            
            # Скорость: v = dx / dt
            velocity_y = np.diff(self.real_history) / dt_array
            
            # Ускорение: a = dv / dt
            acceleration_y = np.diff(velocity_y) / dt_array[:-1]
            
            # Отрисовываем графики по актуальной оси времени
            self.curve_target.setData(self.time_history, self.target_history)
            self.curve_real.setData(self.time_history, self.real_history)
            
            # У производных массивы короче на 1 и 2 элемента соответственно
            self.curve_velocity.setData(self.time_history[:-1], velocity_y)
            self.curve_acceleration.setData(self.time_history[:-2], acceleration_y)

    def closeEvent(self, event):
        self.sock.close()
        super().closeEvent(event)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = LivePhysicsPlot()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
