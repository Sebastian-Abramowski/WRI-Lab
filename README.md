## Dokumentacja projektu

- Przedmiot: Wstęp do robotyki dla informatyków

- Data: 18/05/2025

- Autorzy:

  - Sebastian Abramowski

  - Aleksander Stanoch

- Repozytorium: https://github.com/Sebastian-Abramowski

### Konstrukcja robota

TODO: Opis konstrukcji (rodzaj bazy jezdnej, rozmieszczenie silników i czujników na robocie i względem siebie, wybór rozmiaru kół i gąsienic) + zdjęcia

### Algorytm Linefollowera

Zastosowaliśmy prosty, klasyczny algorytm oparty na dwóch czujnikach koloru umieszczonych z przodu robota, po obu stronach linii.

Gdy oba czujniki widzą kolor biały, oznacza to, że między nimi znajduje się linia (czyli kolor czarny), dlatego robot kontynuuje jazdę prosto. Jeśli oba czujniki widzą czarny, traktujemy to jako skrzyżowanie — również w tym przypadku robot jedzie prosto.

Jeśli prawy czujnik wykryje czarny kolor, oznacza to, że robot zjeżdża z linii w lewo — należy wtedy skręcić w prawo. Analogicznie, gdy lewy czujnik wykryje czarny, robot koryguje tor jazdy skrętem w lewo.

Prędkości kół zostały dobrane eksperymentalnie tak, aby zapewnić stabilną jazdę oraz możliwość pokonywania zakrętów bez wypadania z trasy.

Program znajduje się w pliku `linefollower.py`

Schemat blokowy algorytmu:

<img src="./img/linefollower_flowchart.png" alt="linefollower" width="500">

#### Wykrywanie kolorów przy algorytmie Linefollowera

Ponieważ linefollower wymagał rozpoznawania tylko dwóch kolorów — czarnego i białego — zastosowaliśmy prostą metodę opartą na analizie wartości RGB zwracanych przez czujniki. Jeśli wartości były niejednoznaczne, wspomagaliśmy się nazwą koloru (color_name) zwracaną przez czujnik. Kolory podobne do czarnego (np. "Black", "Brown") traktowaliśmy jako czarny, a kolory jasne (np. "White", "Yellow") jako biały.

Takie podejście było wystarczająco niezawodne — podczas działania linefollowera nie napotkaliśmy większych problemów z wykrywaniem kolorów.

Kod rozpoznawania kolorów:

```python
def get_color_from(sensor):
	red, green, blue = sensor.rgb

	if red > 90 and green > 170 and blue > 100:
		return Color.WHITE

	if red < 35 and green < 65 and blue < 35:
		return Color.BLACK

	if sensor.color_name in ["Black", "Brown"]:
		return Color.BLACK

	if sensor.color_name in ["White", "Yellow", "Blue", "Green"]:
		return Color.WHITE

	return Color.UNKNOWN
```

### Algorytm Transportera

W przeciwieństwie do prostego linefollowera, algorytm transportera wymagał znacznie bardziej złożonego podejścia. Jego zadaniem było samodzielne przejechanie robota przez trasę, rozpoznanie miejsca odbioru i miejsca docelowego, a także wykonanie odpowiednich manewrów skręcania i chwytania obiektu.

Podstawą działania transportera był automat skończony z 20 stanami, w którym każdy stan odpowiadał konkretnemu etapowi misji — np. jazda po linii, wykrycie punktu odbioru, skręt w lewo/prawo, chwycenie przedmiotu, zawrócenie, dotarcie do punktu docelowego i oddanie obiektu.

W ramach niektórych stanów wykorzystaliśmy fragmenty kodu zaimplementowanego wcześniej w linefollowerze — głównie do jazdy po linii między punktami.

Cały proces opierał się na analizie kolorów odczytywanych z dwóch czujników, przechodzeniu między stanami automatu oraz odpowiednim sterowaniu silnikami kół i chwytaka.

Program znajduje się w pliku transporter.py

Automat skończony wykorzystany w algorytmie:

<img src="./img/transporter_finite_state_machine.png" alt="transporter" width="500">

#### Wykrywanie kolorów przy algorytmie Transportera

Ze względu na konieczność rozróżniania kilku kolorów, a także fakt, że błędne rozpoznanie mogło prowadzić do przejścia w niewłaściwy stan, zastosowaliśmy dokładniejszą metodę wykrywania.

Każdy odczyt RGB porównywany był z zestawem wcześniej zdefiniowanych kolorów bazowych. Wybieraliśmy ten kolor, dla którego suma różnic składowych RGB była najmniejsza. Kolory nieistotne (np. żółty, niebieski) traktowaliśmy jako biały, a dla zielonego wprowadziliśmy dodatkową korektę.

Kod rozpoznawania kolorów:

```python
COLOR_BASES = {
    Color.RED:   (125, 35, 15),
    Color.BLUE:  (20, 80, 90),
    Color.BLACK: (22, 38, 20),
    Color.WHITE: (150, 225, 162),
    Color.GREEN: (17, 100, 30),
    Color.YELLOW: (170, 235, 33)
}

def get_color_from_V2(sensor):
    red, green, blue = sensor.rgb
    debug_print("RGB values: ", red, green, blue)

    def avg_diff(color1, color2):
        return (abs(color1[0] - color2[0]) + abs(color1[1] - color2[1]) + abs(color1[2] - color2[2]))

    best_color = Color.UNKNOWN
    best_score = float('inf')

    for color, base in COLOR_BASES.items():
        score = avg_diff(sensor.rgb, base)
        if score < best_score:
            best_score = score
            best_color = color

    # ignore
    if best_color in [Color.BLUE, Color.YELLOW]:
        best_color = Color.WHITE

    # correction
    if best_color == Color.GREEN and (green < 83 or red > 30):
       best_color = Color.WHITE

    return best_color

```

### Napotkane problemy

#### Problemy ogólne

- przy niektórych uruchomieniach robot zdawał się wolniej reagować na kolory

- zarówno przy rozpoznawaniu linii, jak i w trakcie transportu zdarzało się błędne rozpoznanie koloru w niektórych sytuacjach; radziliśmy sobie z tym, dostosowując kod na podstawie analizy tych pojedynczych przypadków

#### Problemy z linefollowerem

- na początku w linefollowerze próbowaliśmy skręcać, ustawiając prędkość tylko na jedno koło, a drugie pozostawiając w miejscu; jednak robot nie radził sobie wtedy z ostrymi zakrętami — dopiero zastosowanie przeciwstawnych obrotów kół podczas korekty pozwoliło skutecznie pokonywać trudniejsze łuki i zapobiegało blokowaniu się robota w powtarzających się sekwencjach ruchów

- podczas testowania linefollowera zauważyliśmy, że szerokość rozstawu czujników koloru ma istotny wpływ na działanie robota; dlatego zmodyfikowaliśmy konstrukcję, aby umożliwić łatwą regulację ich rozmieszczenia po obu stronach

- dużym problemem było odpowiednie dobranie prędkości przy rozpoznawaniu linii; stopniowo ją zmniejszaliśmy, aż robot zaczął działać poprawnie — kluczowym momentem testów były skręty pod kątem prostym, na których robot najczęściej sobie nie radził przy zbyt dużej prędkości

#### Problemy z transporterem

- podczas transportu rozpoznawanie kolorów było szczególnie problematyczne, ponieważ należało odróżniać kilka barw, poza kolorem czarnym i białym (zielony, czerwony, żółty, niebieski); jedno błędne rozpoznanie mogło prowadzić do przejścia w niewłaściwy stan — poradziliśmy sobie z tym, wprowadzając kosztowniejszą obliczeniowo metodę porównywania z zestawem kolorów bazowych i wybierania najbliższego z nich, a także dodając osłonki przy czujnikach, by ograniczyć wpływ światła zewnętrznego na odczyt koloru

- ze względu na nietypowy sposób chwytania obiektu (po bokach), mieliśmy problem z odpowiednią siłą ścisku; rozwiązaliśmy go, modyfikując konstrukcję chwytaka — zmieniliśmy ułożenie zębatek, aby zwiększyć przełożenie

- przy chwytaniu obiektu od boku, chwytak zbyt szybko unosił się do góry; dodaliśmy obciążenie w postaci kół na chwytakach, by spowolnić ruch

- przy skrętach pod kątem prostym w trakcie transportu robot obracał się, aż czujnik wykrywał linię prostopadłą; przy nieco większych prędkościach zdarzało się, że czujnik nie zdążył wykryć koloru i robot skręcał dalej, mimo że nie powinien — ostatecznie rozwiązaliśmy to, po prostu spowalniając cały skręt; testowaliśmy również podejścia z dynamiczną zmianą prędkości skrętu oraz z korektą w przeciwnym kierunku po wykonaniu obrotu
