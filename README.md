# Go vs Rust. Что же лучше в плане конкуретности?

В данном репозиторие представлены бенчмарки для определения скорости работы и
потребления памяти у языков Go и Rust в режиме конкуретности. Для языка Go
проверялась работа **горутин**, а для языка Rust проверялась работа механизма
**async/await** совместно с крейтом **tokio**.


## Реквизиты
 
```
Yoskutik: ~\Desktop\Benchmarks [master] $ go version
go version go1.18.3 windows/amd64

Yoskutik: ~\Desktop\Benchmarks [master] $ rustc --version
rustc 1.62.0 (a8314ef7d 2022-06-27)
```


## Общее описание

Для каждого языка было написано 5 тестов, отвечающих за примерно одинаковую
функциональность, точное описание которых будет представлено далее:
  1. *Sleep*;
  2. *Files R*;
  3. *Files RW*;
  4. *SQLite*;
  5. *MySQL*.

Смысл каждого теста заключается в следующем. В каждом из тестов запускается
*N* конкуретных задач от 10 до 1 млн. (или меньше). Затем производятся замеры
затраченного времени и потребляемой памяти. По затраченному времени можно
судить не только о скорости работы языка, но и том, насколько он страдает
от большого количества конкуретных задач.

Каждый из тестов проводится 5 раз. В качестве метрики скорости работы
используется минимально затраченное время за полный прогон одного теста. В
качестве метрики потребления памяти используется максимальное количество
потребляемой памяти в течение всех 5 прогонов.

<details>
  <summary>
    Почему время записывается минимальное, а потребляемая память максимальная?
  </summary>
  
  Написанные тесты не являются "чистыми", так как запускались на машине, на
  которой помимо тестов работали дополнительные программы - например,
  служебные демоны Windows, драйвер NVIDIA т.п. Если считать, что в тестах
  выполняется идентичная функциональность, то время выполнения будет тогда
  минимальным, когда в системе будет наименьшее влияние от других процессов.
  
  Замеры же памяти проводились напрямую, считывая потребление у запускаемого
  процесса и всех его дочерних процессов. На потребление памяти не должно
  оказывать влияние наличие работающих других программ. Максимальное же
  количество берется исключительно на случай, если в каком-то из тестов
  памяти будет потребляться больше, чем в других.
  
  Однако, не стоит ставить крест на данном бенчмарке из-за того, что тесты
  не являются чистыми. 
</details>

После выполнения каждого теста программа засыпает на время, затраченное на
выполнение теста, умноженное на 1.5. Т.е. если при выполнении 1 теста "Sleep"
программа затратила 0.28 секунд, то перед вызовом следующего теста бенчмарк
дополнительно "заснет" на 0.28 * 1.5 секунд. Это было сделано, чтобы уменьшить
влияние предыдущих тестов на последующие.

В некоторых тестах используются сгенерированные моковые данные. Эти данные
обновляются после каждого отдельного прохода каждого теста.


## 1. Описание теста "Sleep"

Первый тест является "эмулирующим". Каждая корутина выполняет некоторый
рассчет числа в цикле от 1 до 100 тысяч, а затем засыпает на случайное
количество миллисекунд.

Для того, чтобы тесты были повторяемы генерация миллисекунд происходит
при помощи [линейного когурентного генератора](https://wiki) (далее ЛКГ).
Таким образом у каждой корутины будет вызываться разная задержка, однако в
разных тестах задержки будут использованы одни и те же.


## 2. Описание теста "Files R"

Для второго теста было сгенерировано 20 файлов. В каждом из файлов находится
по 3, 6, 9, 12 и т.д. строчек длинной 64 символа (включая символ переноса
строки). При этом в работе теста также использовался ЛКГ, для того, чтобы
файлы читались в случайной последовательности.

Сам тест заключается в том, что каждая корутина читает информацию из файла
и записывает сохраняет её - в канал (в случае Go) или в вектор (в случае Rust).


## 3. Описание теста "Files RW"

Для третьего теста так же использовались текстовые и данные и ЛКГ, однако в
нем в половине случаев в файл записывается дополнительная информация, после чего
файл считывается во всех случаях.

"Files RW" запускается при количестве корутин до 100 тыс. корутин.


## 4. Описание теста "SQLite"

Для четвертого теста была подготовлена база данных SQLite, содержащая одну таблицу
с 4 столбцами и 10 тыс. записями. В тесте снова используется ЛКГ. В зависимости
от случайного значения корутина либо обновляет одну запись в таблице и записывает
её обновленное значение, либо получает все записи с определенным фильтром и
сортировкой.

Так как база данных SQLite не предназначена для высоконагруженных систем,
тестирование проводилось на 10, 100 и 1000 корутин.


## 5. Описание теста "MySQL"

Приницы работы MySQL и SQLite довольно сильно отличаются. Поэтому было решено
провести дополнительно провести тест с MySQL. База данных в пятом тесте дублирует
структуру базы данных SQLite. Функциональность также скопирована с 4го теста.

Единственное отличие тестов в том, что 5й тест дополнительно проводится на 10 и 100
тысячах корутин. Тест 1 млн. корутин не запускается исключительно из-за того, что
на него уходит слишком много времени.


---


## Запуск бенчмарка

При желании вы можете запустить бенчмарк на собственном железе и/или с другими
версиями языков. Для этого запустите скрипт `run.py`, находясь в корневой
директории репозитория.

```
python run.py
```
