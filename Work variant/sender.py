# sender.py
import socket
import time
import math

def main():
    print("Запуск отправителя координат пьезопривода по UDP...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_addr = ("127.0.0.1", 5005)
    
    start_time = time.time()
    try:
        while True:
            t = time.time() - start_time
            
            # 1. Заданное положение (скачки 0 или 5 каждые 2 секунды)
            target_pos = 5.0 if (int(t) % 4 < 2) else 0.0
            
            # 2. Реальное положение (моделируем инерцию и переходной процесс)
            # Добавим затухающие высокочастотные колебания, чтобы увидеть их на графиках скорости/ускорения
            real_pos = target_pos + math.sin(t * 15) * 0.4 * math.exp(-(t % 2) * 2)
            
            # Отправляем три параметра: Время, Целевое_Положение, Реальное_Положение
            message_str = f"{t},{target_pos},{real_pos}"
            sock.sendto(message_str.encode('utf-8'), server_addr)
            
            # Пауза 10 миллисекунд (высокая скорость отправки точек)
            time.sleep(0.01) 
            
    except KeyboardInterrupt:
        print("\nОстановка отправителя.")
    finally:
        sock.close()

if __name__ == '__main__':
    main()


