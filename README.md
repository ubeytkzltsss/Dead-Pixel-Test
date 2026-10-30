# Dead Pixel Test

Ekranında **ölü veya takılı piksel** var mı, saniyeler içinde öğren.

## Hemen kullan

### Web sürümü — tek dosya

**https://deadpixeltest.netlify.app/**

Web sürümünün tamamı tek bir [`index.html`](index.html) dosyasındadır:
HTML, CSS, JavaScript, favicon bu dosyanın içindedir. 
Harici CSS/JS/görsel dosyası yoktur; indirip çift tıklaman yeterli.
Monitör, telefon, tablet, laptop ve Smart TV tarayıcılarında çalışır.

### Masaüstü sürümü — tek Python dosyası

```bash
python3 dead_pixel_test.py
```

Windows'ta:

```powershell
py dead_pixel_test.py
```

Python 3.8+ ve standart `tkinter` yeterlidir; ek paket gerekmez.



## Özellikler

- 22 test deseni: düz renkler, gradyanlar, renk çubukları, dama, 1px dama,
  ızgara, hareketli çubuk ve ters çevirme deseni
- Takılı piksel onarıcı
- Ayarlanabilir otomatik renk geçişi
- Tam ekran ve ekranı uyanık tutma desteği
- Kendiliğinden gizlenen test arayüzü ve imleç
- Klavye, fare, dokunmatik ve TV kumandası kontrolleri
- Türkçe / İngilizce arayüz
- `#red`, `#black` gibi doğrudan desen bağlantıları

## Kontroller

| Tuş / hareket | İşlev |
|---|---|
| `→` / `←`, tık, sağ tık, kaydırma | Sonraki / önceki desen |
| `Space` | Otomatik geçiş |
| `F` | Tam ekran |
| `H` | Arayüzü gizle/göster |
| `L` | Desen listesi |
| `1`–`9` | Desene hızlı git |
| `Esc` / `Q` | Çıkış |

Masaüstü seçenekleri için:

```bash
python3 dead_pixel_test.py --help
python3 dead_pixel_test.py --list
python3 dead_pixel_test.py --auto 3 --pattern red
```

## Nasıl test edilir?

1. Ekranı yumuşak bir bezle temizle; toz, ölü piksel sanılabilir.
2. Parlaklığı %100'e al, karanlık bir ortam kullan ve yakınlaştırmayı %100 yap.
3. Her rengi yavaşça tara. Siyah ekranda parlayan nokta takılı piksel,
   renkli ekranda siyah kalan nokta ölü pikseldir.
4. Takılı pikselde onarıcıyı 10–20 dakika çalıştırmayı deneyebilirsin.
   Tamamen ölü piksel donanım arızasıdır ve yazılımla onarılamaz.

> **Uyarı:** Onarıcı ve ters çevirme deseni hızla yanıp sönen ışık içerir.
> Epilepsi veya ışığa duyarlılığın varsa bu modları kullanma.

## Dosya yapısı

```text
Dead-Pixel-Test/
├── LICENSE
├── README.md
├── dead_pixel_test.py            # tek dosyalık masaüstü sürümü
└── index.html                    # tek dosyalık web sürümü
```



## English summary

The complete web app is self-contained in `index.html`: open it in any browser
and inspect 22 fullscreen patterns for dead or stuck pixels. A dependency-free
single-file Python/Tkinter desktop edition is included in
`dead_pixel_test.py`.


<p align="center">
<img width="100" height="99" alt="resim" src="https://github.com/user-attachments/assets/7e14465d-bdef-421e-bc16-199a8646792e" />
</p>

<p align="center">
  Developed by <b>Ubeyt</b>.
</p>
