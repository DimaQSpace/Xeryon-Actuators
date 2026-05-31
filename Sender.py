# sender.py
import socket
import time
import math

def main():
    print("Запуск отправителя с физической моделью пьезопривода по UDP...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_addr = ("127.0.0.1", 5005)
    
    # --- ФИЗИЧЕСКИЕ ПАРАМЕТРЫ ПЬЕЗОДВИГАТЕЛЯ ---
    f_n = 5.0      # Собственная частота резонанса (для наглядности на графике сделаем 5 Гц)
    zeta = 0.15    # Коэффициент демпфирования (0.15 - слабая амортизация, будет виден "звон")
    
    # Шаг времени симуляции (совпадает с нашей паузой sleep)
    dt = 0.01  
    
    # Коэффициенты дискретного уравнения второго порядка (преобразование Тастина / Эйлера)
    omega_n = 2 * math.pi * f_n
    denom = 1 + 2 * zeta * omega_n * dt + (omega_n * dt) ** 2
    
    a1 = (2 + 2 * zeta * omega_n * dt) / denom
    a2 = -1 / denom
    b0 = ((omega_n * dt) ** 2) / denom
    
    # Стартовые условия для дифференциального уравнения
    real_pos = 0.0
    prev_real_pos1 = 0.0
    prev_real_pos2 = 0.0
    
    start_time = time.time()
    try:
        while True:
            t = time.time() - start_time
            
            # --- ЗАДАННОЕ ПОЛОЖЕНИЕ (Цель) ---
            # Вернем прямоугольные скачки (0 и 5 ед.), чтобы четко увидеть переходной процесс
            target_pos = 5.0 if (int(t) % 4 < 2) else 0.0
            
            # --- УПРОЩЕННАЯ МОДЕЛЬ ВТОРОГО ПОРЯДКА ---
            # Вычисляем новое реальное положение на основе двух предыдущих шагов
            real_pos = a1 * prev_real_pos1 + a2 * prev_real_pos2 + b0 * target_pos
            
            # Обновляем историю шагов для следующей итерации
            prev_real_pos2 = prev_real_pos1
            prev_real_pos1 = real_pos
            
            # Отправляем данные на график
            message_str = f"{t},{target_pos},{real_pos}"
            sock.sendto(message_str.encode('utf-8'), server_addr)
            
            time.sleep(dt) # Шаг 10 мс
            
    except KeyboardInterrupt:
        print("\nОстановка отправителя.")
    finally:
        sock.close()

if __name__ == '__main__':
    main()
