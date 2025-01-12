import random
import time
import json
from datetime import datetime
import threading
import re


class Oyuncu: #Oyuncunun özellikleri
    def __init__(self, isim):
        self.isim = isim # Oyuncunun adı
        self.puan = 0 #Oyuncunun başlangıç puanı
        self.sure = 100 #Oyuncunun başlangıç süresi
        self.dogru_cevaplar = []
        self.yanlis_cevaplar = []
        self.kategori_istatistikleri = {"Fizik": 0, "Kimya": 0, "Biyoloji": 0}
        self.timer_active = True #Zamanlayıcı aktiflik durumu
 
    def puan_ekle(self, miktar): #Puan ekleme 
        self.puan += miktar

    def sure_azalt(self): #Zamanlayıcı
        while self.timer_active and self.sure > 0:
            time.sleep(1)
            self.sure -= 1
        return self.sure > 0

    def cevap_kaydet(self, soru, cevap, dogru_mu, kategori): #Cevap kaydetme
        if dogru_mu:
            self.dogru_cevaplar.append({"soru": soru, "cevap": cevap})
            self.kategori_istatistikleri[kategori] += 1
        else:
            self.yanlis_cevaplar.append({"soru": soru, "cevap": cevap})

class Kategori:
    def __init__(self, isim, sorular):
        self.isim = isim #Kategoriinin adı
        self.sorular = sorular # Soru listesi kategoriye ait

class OyunYoneticisi:
    def __init__(self):
        self.yuksek_skorlar = self.yuksek_skorlari_yukle() # Yüksek skorları yükler
        
    def yuksek_skorlari_yukle(self):
        try:
            with open("yuksek_skorlar.json", "r", encoding="utf-8") as f:
                return json.load(f) #Yüksek skoları dosyadan yükleme
        except FileNotFoundError:
            return []

    def yuksek_skoru_kaydet(self, oyuncu): #Yüksek skorları kaydeder
        tarih = datetime.now().strftime("%Y-%m-%d %H:%M") #Skor Tarihi
        skor = {
            "isim": oyuncu.isim,
            "puan": oyuncu.puan,
            "tarih": tarih,
            "kategori_istatistikleri": oyuncu.kategori_istatistikleri
        }
        self.yuksek_skorlar.append(skor)
        self.yuksek_skorlar.sort(key=lambda x: x["puan"], reverse=True) #Skorları büyükten küçüğe sırala
        self.yuksek_skorlar = self.yuksek_skorlar[:10] #10 skoru tutar
        
        with open("yuksek_skorlar.json", "w", encoding="utf-8") as f:
            json.dump(self.yuksek_skorlar, f, ensure_ascii=False, indent=2) #3 ocak buraya kadar

# Cevap kontrol fonksiyonu: Kullanıcı cevaplarının doğruluğunu ve formatını kontrol eder
def cevap_kontrol(cevap):
    if not cevap.strip():  # Boş cevap kontrolü
        return False, "Boş cevap veremezsiniz!"
    if cevap.strip().isdigit():  # Sayısal cevap kontrolü
        return True, cevap.strip()
    if not re.match("^[a-zA-ZğüşıöçĞÜŞİÖÇ ]+$", cevap):  # Geçersiz karakter kontrolü
        return False, "Lütfen sadece harf kullanın!"
    return True, cevap.strip().lower()

def quiz_yap(oyuncu, kategoriler):
    sorulan_sorular = [] #Soru listesi
    ipucu_hakki = 3 #Oyuncun ipucu hakkı 
    pas_hakki = 2 #Oyuncunun pas hakkı
    kullanilan_ipucu = set() # Kullanılan ipuçlarının listesi

    timer_thread = threading.Thread(target=oyuncu.sure_azalt)
    timer_thread.start() #
    
    for i in range(10): # 10 soru sorulur for bunu döndürür
        if oyuncu.sure <= 0: #Süre biterse oyun durur.
            print(f"\nMaalesef süreniz doldu {oyuncu.isim}!")
            break

        print(f"\n{i+1}. Soru ({oyuncu.isim}) - Kalan süre: {int(oyuncu.sure)} saniye") # Soruyu ve Kalan süreyi gösterir
        print(f"İpucu Hakkı: {ipucu_hakki} | Pas Hakkı: {pas_hakki}") #Kalan pas hakkı ve kalan ipucu hakkını gösterir
        
        kategori = random.choice(kategoriler) #Oyun rastgele bir kategori seçer
        while True:
            soru = random.choice(kategori.sorular) #Oyun seçtiği kategoriden rastgele soru sorar
            soru_metni = soru["soru"]
            if soru_metni not in [s["soru"] for s in sorulan_sorular]: #Daha önce sorulmuş soruları kontrol eder
                sorulan_sorular.append(soru)
                break   

        print(f"{kategori.isim} - {soru['soru']}")
        soru_id = len(sorulan_sorular) - 1
        
        while True:
            if oyuncu.sure <= 0:
                print(f"\nMaalesef süreniz doldu {oyuncu.isim}!")
                break 

            komut = input("Cevap vermek için cevabınızı yazın, ipucu için 'i', pas için 'p' yazın: ").strip().lower() #Kullanıcıdan ipucu ya da pas komutu sorulur
            
            if komut == 'i' and ipucu_hakki > 0 and soru_id not in kullanilan_ipucu:
                ipucu = soru["cevap"][:2] + "..." if len(soru["cevap"]) > 3 else soru["cevap"][:1] + ".." #Cevap 3 karakterden uzunsa cevabın ilk iki karakterini alıp sonuna üç nokta koyar
                print(f"İpucu: Cevap {ipucu} ile başlıyor") # Eğer cevap üç arakterden kısa veya eş ise ilk bir karakterini alır iki nokta ekler
                ipucu_hakki -= 1
                kullanilan_ipucu.add(soru_id)
                continue
            elif komut == 'p' and pas_hakki > 0: #Eğer pas hakkı 0 dan büyükse sorunun doğru cevabı gözükür ve pas hakkı bir azalır
                print(f"Soru pas geçildi. Doğru cevap: {soru['cevap']}")
                pas_hakki -= 1
                break
            else:       
                # Cevap kontrolü kullanıcı doğru mu yanlış mı girdi ipucu aldı mı aldıysa kaç puan aldı 
                gecerli, temiz_cevap = cevap_kontrol(komut)
                if not gecerli:
                    print(temiz_cevap)  #  Soru hatalı cevap verilir ise doğru cevabı yazdırır
                    continue
                  
                if temiz_cevap == soru["cevap"].lower():
                    print("Doğru!")
                    puan = 5 if soru_id in kullanilan_ipucu else 10 #Kullanıcı ipucu alırsa kazandığı puanı düşürür
                    oyuncu.puan_ekle(puan)
                    print(f"Bu sorudan {puan} puan kazandınız!")
                    oyuncu.cevap_kaydet(soru["soru"], temiz_cevap, True, kategori.isim)
                else:
                    print(f"Yanlış! Doğru cevap: {soru['cevap']}")
                    oyuncu.cevap_kaydet(soru["soru"], temiz_cevap, False, kategori.isim)
                print(f"Açıklama: {soru['aciklama']}")
                break

    oyuncu.timer_active = False # Zamanlıyıcı durdur
    timer_thread.join() #Thread sonlanır

    # Oyuncu performansını detaylı rapolar
def oyun_raporu_olustur(oyuncu): 
    print(f"\n=== {oyuncu.isim} için Oyun Raporu ===")
    print(f"Toplam Puan: {oyuncu.puan}")
    print("\nKategori Bazlı Başarı:")
    for kategori, dogru_sayisi in oyuncu.kategori_istatistikleri.items():
        print(f"{kategori}: {dogru_sayisi} doğru")
    
    print("\nDoğru Cevaplanan Sorular:")
    for dogru in oyuncu.dogru_cevaplar:
        print(f"- {dogru['soru']}")
    
    print("\nYanlış Cevaplanan Sorular:")
    for yanlis in oyuncu.yanlis_cevaplar:
        print(f"- {yanlis['soru']} (Cevabınız: {yanlis['cevap']})") #7 ocak buraya kadar 


def cevap_kontrol(cevap):   
    if not cevap.strip(): # Boş girişini kontrol etme yeri
        return False, "Boş cevap veremezsiniz!"
    
    # Komut kontrolü ('i' ve 'p' için)
    if cevap.strip() in ['i', 'p']:
        return True, cevap.strip()
    
    # Sayı içeriyor mu içermiyor mu
    if any(karakter.isdigit() for karakter in cevap):
        return False, "Üzgünüm, cevaplarda sayı kullanılmamalıdır. Lütfen sadece harf kullanarak cevap veriniz."
    
    # harf ve boşluk mu sadece onun kontrolü
    if not re.match("^[a-zA-ZğüşıöçĞÜŞİÖÇ ]+$", cevap):
        return False, "Lütfen sadece Türkçe karakterler ve Latin alfabesi kullanın!"
    
    return True, cevap.strip().lower() 


#Kategori halinde bulunan soru havuzu
kategoriler = [
    Kategori("Fizik", [
         {"soru": "Uzunluğun SI birim sistemindeki sembolü nedir?",
           "cevap": "m",
             "aciklama": "Uzunluğun SI birim sisteminde m harfi olarak ifade edilir."},
         {"soru": "Düzgün doğrusal harekette x-t grafiğinde hangi şekil olamaz",
            "cevap": "Eğri",
              "aciklama": "X-T doğrusal harekette eğri grafikler olamaz doğrusal çizgiler olur."},
              {"soru": "Duran bir cismi hareket ettirebilen, hareket hâlindeki bir cismi durdurabilen veya cisimlerin şeklini değiştirebilen etkiye ne denir.",
            "cevap": "Kuvvet",
              "aciklama": "Kuvvet duran bir cismi harekette ettirebilir hareket halindekini durdurabilir ya da cisimlerin şeklini değiştirebilir."},
         {"soru": "Kristal özelliğe sahip maddeleri inceleyen fiziğin alt dalına ne denir",
            "cevap": "Katıhal",
              "aciklama": "Kathıal fiziği kristal özelliğe sahip maddeleri inceler."},
         {"soru": "Madde ve enerji arasındaki ilişkileri inceleyen bilim dalının ismi nedir ",
            "cevap": "Fizik",
              "aciklama": "Madde ve enerji arasındaki ilişkileri inceleyen bilim dalı fiziktir."},
         {"soru": "Fiziğin altdallarından ışığın diğer maddelerle etkileşimini inceleyen bilim dalı nedir?",
           "cevap": "Optik",
             "aciklama": "Fiziğin ışığın ölçümünü ve sınıflandırması ile uğraşan fiziğin bir alt dalıdır."},
         {"soru": "Fiziğin altdallarından ısı enerjisiyle ilgili konuları olan fiziğin alt dalı nedir?",
           "cevap": "Termodinamik",
             "aciklama": "ısı enerjisiyle kinetik enerji arasındaki ilişkileri ve bu konuyla ilgili olayları konu alan fizik dalı"},
         {"soru": "Termodinamik fiziğin alt dallarından mıdır?",
            "cevap": "Evet",
              "aciklama": "Termodinamik fiziğin en büyük alt dallarından biridir."},
         {"soru": "Gücün SI Birim sistemindeki sembolü nedir?",
            "cevap": "W",
              "aciklama": "Gücün simgesi P power olarak geçer ama SI Birim sisteminde watt yani W dir"},
        {"soru": "Maddelerde ısı akışı nereden başlar?",
            "cevap": "sıcaktan",
              "aciklama": "Maddelerin ısı akışı sıcak taraftan soğuk tarafa doğru akar."},
        {"soru": "Hız temel bir büyüklük müdür ?",
            "cevap": "Hayır",
              "aciklama": "Hız temel değil türetilmiş bir büyüklüktür."},
        {"soru": "Bir cismin konumunun zamana göre değişimine ne ad verilir?",
           "cevap": "hareket",
             "aciklama": "Bir cismin yer değiştirmesi hareket olarak adlandırılır."},
        {"soru": "Maddelerde ısı iletirken kesit alanı artarsa iletim hızı nasıl değişir? ",
             "cevap": "Artar",
               "aciklama": "Isı iletiminde kullanılan maddenin kesit alanı (A) artırılırsa enerji iletim hızı artar."},
        {"soru": "Maddelerde ısı iletirken uzunluk artarsa iletim hızı nasıl değişir? ",
             "cevap": "Azalır",
               "aciklama": "Isı iletiminde kullanılan malzemenin boyu (L) artırılırsa enerji iletim hızı azalır. Enerji iletim hızı maddenin uzunluğu ile ters orantılıdır."},
        {"soru": "Lisede Dünya'nın yer çekimi ivmesi kaç olarak kabul edilir?  ",
          "cevap": "on",
            "aciklama": "Dünya'daki yer çekimi ivmesi lise müfredatında 10 olarak kabul edilir"},
        {"soru": "Elektrik devresinde akımı ölçen cihaza ne denir?",
          "cevap": "ampermetre",
            "aciklama": "Ampermetre, elektrik akımını ölçer."},
        {"soru": "Kütle biriminin SI birim sistemindeki karşılığı nedir?",
          "cevap": "kilogram",
            "aciklama": "Kütle birimi kilogram (kg) olarak ifade edilir."},
        {"soru": "Sürtünmesiz ortamda hareket eden cisim ne yapar?",
          "cevap": "sabit hız",
            "aciklama": "Sürtünmesiz ortamda cisim sabit hızla hareket eder."},
        {"soru": "Işığın boşlukta en hızlı yayıldığı ortam nedir?",
          "cevap": "vakum",
            "aciklama": "Işık en hızlı vakumda yayılır."},
        {"soru": "Bir cismin kütlesi dünyanın her yerinde aynı mıdır?",
          "cevap": "evet",
            "aciklama": "Kütle, dünyanın her yerinde sabittir."},
        {"soru": "Enerji dönüşümünü sağlayan cihazın adı nedir?",
          "cevap": "jeneratör",
            "aciklama": "Jeneratör, mekanik enerjiyi elektrik enerjisine dönüştürür."},
        {"soru": "Termodinamiğin birinci yasası nedir?",
          "cevap": "enerjinin korunumu",
            "aciklama": "Termodinamiğin birinci yasasına göre enerji yoktan var edilemez, var olan enerji yok edilemez."},
        {"soru": "Yüksek sıcaklıkta bir gazın hacmi nasıl değişir?",
          "cevap": "artar",
            "aciklama": "Sıcaklık arttıkça gazın hacmi de artar."},
        {"soru": "Ses dalgalarının en hızlı yayıldığı ortam nedir?",
          "cevap": "katı",
            "aciklama": "Ses, katı ortamda daha hızlı yayılır."},
        {"soru": "Bir cismin hızının artması hangi kuvvetle mümkündür?",
          "cevap": "net kuvvet",
            "aciklama": "Hız artışı net kuvvetin etkisiyle olur."},
        {"soru": "Elektriksel potansiyel simgesi nedir?",
          "cevap": "V",
            "aciklama": "Elektriksel potansiyel enerji, bir yük ile elektrik alan arasındaki ilişkiye bağlıdır."},
        {"soru": "Bir cismin hızındaki değişim hangi büyüklükle ölçülür?",
          "cevap": "ivme",
            "aciklama": "İvme, hızdaki değişimin zamana oranıdır."},
        {"soru": "Elektriksel yüklerin hareketine ne ad verilir?",
          "cevap": "akım",
            "aciklama": "Elektriksel yüklerin hareketi elektrik akımı olarak adlandırılır."},
        {"soru": "Bir cismin enerjisini ölçen birim nedir?",
          "cevap": "joule",
            "aciklama": "Enerji birimi joule (J) olarak ifade edilir."},
        {"soru": "Isı iletimi hangi ortamda daha hızlıdır?",
          "cevap": "katı",
            "aciklama": "Isı katı maddelerde daha hızlı iletilir."},
        {"soru": "Fiziksel değişimle kimyasal değişim arasındaki fark nedir?",
          "cevap": " madde yapısı",
            "aciklama": "Kimyasal değişimde madde yapısı değişirken, fiziksel değişimde sadece görünüş değişir."},
        {"soru": "Fotosentez sırasında bitkilerin ürettiği gaz nedir?",
          "cevap": "oksijen",
            "aciklama": "Fotosentez sırasında bitkiler oksijen gazı üretir."},
        {"soru": "Bitkilerde su taşımakla görevli doku nedir?",
          "cevap": "ksilem",
            "aciklama": "Ksilem, bitkilerde suyun taşınmasını sağlar."},
        {"soru": "İnsan vücudunda kanı temizleyen organ nedir?",
          "cevap": "böbrek",
            "aciklama": "Böbrek, kanı temizleyen organdır."},
        {"soru": "Bir cisim hareket etmiyorsa, üzerine hangi kuvvet etki eder?",
          "cevap": "durgun",
            "aciklama": "Bir cisim hareket etmiyorsa, üzerine etki eden kuvvetler dengededir."},
        {"soru": "Yön ve doğrultusu olmayan niceliklere ne denir?",
          "cevap": "Skaler",
            "aciklama": "Kütle, Sürat, Enerji gibi nicelikler skaler yani yönsüz kuvvetler olarak sınıflandırılır."},
        {"soru": "Yön ve doğrultusu olan niceliklere ne denir?",
          "cevap": "Vektörel",
            "aciklama": "Kuvvet, Hız gibi nicelikler vektörel yani yönlü kuvvetler olarak sınıflandırılır."},
        {"soru": "Bir cismin potansiyel enerjisi hangi faktörlere bağlıdır?",
          "cevap": "yükseklik",
            "aciklama": "Bir cismin potansiyel enerjisi, cismin yerden yüksekliğine bağlıdır."},
        {"soru": "Bir meyve sayesinde kütle çekimini bulan bilim insanı kimdir ",
          "cevap": "Newton",
            "aciklama": "Issac Newton ın kafasına elma ağacından elma düşer ve o zaman her şeyin farkında varır."},
        {"soru": "Doğada kaç tane temel kuvvet vardır.",
            "cevap": "dört",
              "aciklama": "Doğada 4 tane temel kuvvet vardır. Kütle çekim, Zayıf nükleer, Güçlü nükleer, Elektromanyetik kuvvettir."}

    ]),
    Kategori("Kimya", [
        {"soru": "Elementlerin düzenli sıralandığı tabloya ne ad verilir?",
           "cevap": "periyodik tablo",
            "aciklama": "Periyodik tablo, elementlerin özelliklerine göre sıralandığı bir tablodur."},
        {"soru": "Metallerin ametallerle elektron alışverişi sonucu ... bağ oluşur?",
           "cevap": "Kovalent",
             "aciklama": "Metaller ametallerle elektron alışverişi yapar bunun sonucunda kovalent bağ oluşur."},
             {"soru": "Periyodik cetvelde 7A grubunun adı nedir?",
           "cevap": "Halojenler",
             "aciklama": "Periyodik cetvelde 7A grubuna halojenler denir. Son katmanlarında 7 elektron vardır."},
             {"soru": "HCL nin yaygın adı nedir",
           "cevap": "Tuz ruhu",
             "aciklama": "HCL nin halk arasındaki yaygın adı tuz ruhudur."},
        {"soru": "Atomların elektron alarak veya vererek soygaz elektron düzenine ulaşmasına ne denir? ",
           "cevap": "oktet",
             "aciklama": "Atomların elektron alarak veya vererek soygaz elektron düzenine ulaşmasına oktet dizilimi denir."},
        {"soru": "Dünya atmosferine hapsederek küresel ısınmaya neden olan gaza ne denir?",
           "cevap": "Sera gazı",
             "aciklama": "Sera gazları dünyanın atmosferinde çoğalarak dünyanın ısınmasına neden olur."}, 
        {"soru": "Mumun erimesi nasıl bir olaydır?",
           "cevap": "Fiziksel",
             "aciklama": "Mumun erimesi fiziksel bir olaydır sadece hal değiştirir."},
        {"soru": "Mumun yanması nasıl bir olaydır?",
           "cevap": "Kimyasal",
             "aciklama": "Mumun yanması kimyasal bir olaydır mumun yapısı değişir."},
        {"soru": "Hidrojenin atom numarası kaçtır?",
          "cevap": "Bir",
            "aciklama": "Hidrojen periyodik tablodaki ilk elementtir."},
        {"soru": "Atomu üzümlü keke benzeten bilim insanı kimdir?",
          "cevap": "Thomson",
            "aciklama": "Thomson atomu üzümlü keke benzetmiştir."},
        {"soru": "Yoğunluk nelere bağlıdır. Simgelerini aralarına bir boşluk olacak şekilde yan yana yazınız",
          "cevap": "m v",
            "aciklama": "Yoğunluk formülü d=m/V dir. kütle ve hacime bağlıdır. "},
        {"soru": "Saf maddeler kaça ayrılır?",
          "cevap": "iki",
            "aciklama": "Saf maddeler elementler ve bileşikler olmak üzere ikiye ayrılır."},
        {"soru": " En güçlü kimyasal bağ nedir?",
          "cevap": "Kovalent",
            "aciklama": "İyonik bağ, elektron alışverişi ile oluşan kimyasal bağdır."},
        {"soru": "Asidik çözeltiler hangi pH değerine sahiptir?",
          "cevap": "yedi den küçük",
            "aciklama": "Asidik çözeltilerin pH değeri 7'den küçüktür."},
        {"soru": "Hangi elementin sembolü 'O'dur?",
          "cevap": "oksijen",
            "aciklama": "Oksijen, periyodik tablodaki 8. elementtir ve sembolü 'O'dur."},
        {"soru": "Saf su doğal ortamda bulunur mu?",
          "cevap": "hayır",
            "aciklama": "Saf suyun pH değeri nötrdür ve 7'dir ama bu doğal ortamda olamaz."},
        {"soru": "Elektronlar hangi katmanlarda bulunur?",
          "cevap": "yörüngelerde",
            "aciklama": "Elektronlar, atomik yörüngelerde yer alır."},
        {"soru": "Asidik bir çözelti hangi renk gösterir?",
          "cevap": "kırmızı",
            "aciklama": "Asidik çözeltiler, genellikle pH kağıdında kırmızı renkte görünür."},
        {"soru": "Nükleer enerji kaynağı nedir?",
          "cevap": "uranyum",
            "aciklama": "Nükleer enerji kaynağı olarak uranyum kullanılır."},
        {"soru": "Bir elektronun enerji alıp bu enerjiyi ışık veya foton olarak yaymasına ne denir?",
          "cevap": "emülsiyon",
            "aciklama": "emülsiyon elektronların enerjiyi foton ve ışık olarak yaymasına denir."},
        {"soru": "Helyum elementi kaçıncı periyottadır?",
          "cevap": "Bir",
            "aciklama": "Helyum elementi birinci periyotta hidrojen ile karşılıklı bir konumdadır."},
        {"soru": "Atomun merkezindeki yüksüz parçacığın adı nedir?",
          "cevap": "nötron"
          , "aciklama": "Nötron atomun çekirdeğin içinde yüksüz bir parçacıktır."},
        {"soru": "Elektronlar negatif yüklü müdür?",
          "cevap": "evet", 
          "aciklama": "Elektronlar negatif yük taşır."},
        {"soru": "Asidik çözeltinin pH değeri ne kadar olmalıdır?",
          "cevap": "yedi den küçük",
            "aciklama": "Asidik çözeltilerin pH değeri 7'den küçük olmalıdır."},
        {"soru": "Gaz halinden katı hale geçmeye ne ad verilir?",
          "cevap": "Kırağılaşma",
            "aciklama": "Gaz halinden katı hale geçmeye Kırağılaşma denir."},
        {"soru": "Bazik çözeltiler hangi pH değerine sahiptir?",
          "cevap": "yedi den büyük",
            "aciklama": "Bazik çözeltilerin pH değeri 7'den büyüktür."},
        {"soru": "Atomun pozitif yüklü parçacığına ne ad verilir?",
          "cevap": "proton",
            "aciklama": "Atom çekirdeğinde bulunan pozitif yüklü parçacıklara proton denir."},
        {"soru": "Bir maddenin en küçük yapı taşı nedir?",
          "cevap": "atom",
            "aciklama": "Maddelerin en küçük yapı taşı atomlardır."},
        {"soru": "Suyun kimyasal formülü nedir?",
          "cevap": "H iki O",
            "aciklama": "Su, iki hidrojen ve bir oksijen atomundan oluşur."},
        {"soru": "Elementlerin bir araya gelerek oluşturduğu saf madde nedir?",
          "cevap": "bileşik",
            "aciklama": "Bileşikler, farklı elementlerin birleşmesiyle oluşur."},
        {"soru": "Kimyasal reaksiyonda değişmeyen maddeye ne ad verilir?",
          "cevap": "katalizör", 
          "aciklama": "Katalizör, reaksiyonu hızlandırır ama kimyasal olarak değişmez."},
        {"soru": "Hidrojenin sembolü nedir?",
          "cevap": "H",
            "aciklama": "Hidrojenin kimyasal sembolü H'dir."},
        {"soru": "Kimyasal elementlerin sayısı kaçtır?",
          "cevap": "Yüz On Sekiz",
            "aciklama": "Şu anda bilinen 118 kimyasal element bulunmaktadır."},
        {"soru": "Su hangi elementlerin birleşiminden oluşur?",
          "cevap": "oksijen ve hidrojen",
            "aciklama": "Su, oksijen ve hidrojen elementlerinin birleşimiyle oluşur."},
        {"soru": "Hangi gaz hava ile reaksiyona girerek asidik yağlı çözüntü oluşturur?",
          "cevap": "karbon dioksit",
            "aciklama": "Karbon dioksit, su ile reaksiyona girerek asidik çözüntüler oluşturur."},
        {"soru": "Bir çözeltinin asidik mi bazik mi olduğunu gösteren madde nedir?",
          "cevap": "pH kağıdı",
            "aciklama": "pH kağıdı, çözeltinin asidik veya bazik olduğunu gösteren bir araçtır."},
        {"soru": "Saf su kaç derecede kaynar?",
          "cevap": "yüz",
            "aciklama": "Saf su deniz seviyesinde 100°C'de kaynar."},
        {"soru": "Oksijenin sembolü nedir?",
          "cevap": "O",
            "aciklama": "Oksijenin kimyasal sembolü O'dur."},
        {"soru": "Metallerin çoğu hangi özelliklere sahiptir?",
          "cevap": "iletken",
            "aciklama": "Çoğu metal, elektrik ve ısıyı iletme özelliğine sahiptir."},
        {"soru": "Sıcaklık ne ile ölçülür?",
          "cevap": "Termometre",
            "aciklama": "Sıcaklık termometre cihazı ile ölçülür birkaç çeşidi vardır."}
    ]),
    Kategori("Biyoloji", [ 
            {"soru": "İnsanın genetik bilgisini taşıyan molekül nedir?",
          "cevap": "dna",
            "aciklama": "DNA, genetik bilgiyi taşıyan temel biyolojik moleküldür."},
        {"soru": "Üzerinde ribozom taşıyan Endoplazmik Retikuluma ne denir",
          "cevap": "granüllü endoplazmik retikulum",
            "aciklama": "Bu tip endoplazmik retikulumlar protein sentezinde görevlidirler."},
        {"soru": "İhtiyaç duyduğu besinleri kendi üretebilen canlılara ne nedir?",
           "cevap": "Ototrof",
             "aciklama": "Ototrof canlılar zorunda kaldıkça besinlerini kendi üretebilirler."},
        {"soru": "Sindirim enzimleri bulunan keseye ne denir?",
           "cevap": "Lizozom",
             "aciklama": "Lizozom Sindirim enzimleri bulunduran vucudun önemli parçalarından birisidir "},
        {"soru": "Bitkilerde fotosentez hangi organelde gerçekleşir?",
          "cevap": "kloroplast",
            "aciklama": "Fotosentez, kloroplast organelinde gerçekleşir."},
        {"soru": "Canlılar arasında protein benzerliği artarsa ... derecesi artar",
          "cevap": "akrabalık",
            "aciklama": "Protein benzerliği canlılar için en önemli faktörlerden biridir."},
        {"soru": "Canlıların enerji ihtiyacını karşılayan hücre organeli nedir?",
          "cevap": "mitokondri",
            "aciklama": "Mitokondri, hücrede enerji üretir."},
        {"soru": "Omurgalılar her zaman memeli midir?",
          "cevap": "hayır",
            "aciklama": "Memeliler, omurgalılar sınıfına dahildir."},
        {"soru": "Hücre zarı hangi görevle sorumludur?",
          "cevap": "koruma",
            "aciklama": "Hücre zarı, hücreyi korur ve madde alışverişini düzenler."},
        {"soru": "İnsan vücudunda oksijen taşıyan madde nedir?",
          "cevap": "hemoglobin",
            "aciklama": "Hemoglobin, oksijen taşıyan bir proteindir."},
        {"soru": "Hangi organ vücutta kanı pompalamakla sorumludur?",
          "cevap": "kalp",
            "aciklama": "Kalp, kanı vücuda pompalayan ana organdır."},
        {"soru": "Bitkilerde tohum oluşumunu sağlayan organ nedir?",
          "cevap": "çiçek",
            "aciklama": "Bitkilerde tohum oluşumu çiçek organında gerçekleşir."},
        {"soru": "Kan dolaşımında oksijen taşıyan hücre nedir?",
          "cevap": "alyuvar",
            "aciklama": "Alyuvarlar, kan dolaşımında oksijen taşıyan hücrelerdir."},
        {"soru": "Fotosentez sırasında bitkilerin ürettiği gaz nedir?",
          "cevap": "oksijen",
            "aciklama": "Fotosentez sırasında bitkiler oksijen gazı üretir."},
        {"soru": "Hücrede genetik bilgi taşıyan yapıya ne ad verilir?",
          "cevap": "kromozom",
            "aciklama": "Genetik bilgiyi taşıyan yapılar kromozomlardır."},
        {"soru": "Türden Aleme gidildikçe ortak özellikler nasıl değişir ?",
          "cevap": "Azalır",
            "aciklama": "Türden aleme gidildikçe ortak özellikler azalır çünkü canlı çeşitliliği artar."},
        {"soru": "Bitkilerde su taşımakla görevli doku nedir?",
          "cevap": "ksilem",
            "aciklama": "Ksilem, bitkilerde suyun taşınmasını sağlar."},
        {"soru": "İnsan vücudunda kanı temizleyen organ nedir?",
          "cevap": "böbrek",
            "aciklama": "Böbrek, kanı temizleyen organdır."},
        {"soru": "Proteinlerin yapı taşı nedir?",
          "cevap": "aminoasit",
            "aciklama": "Aminoasitler, proteinlerin temel yapı taşıdır."},
        {"soru": "Kanın pıhtılaşmasını sağlayan madde nedir?",
          "cevap": "fibrin",
            "aciklama": "Fibrin, kanın pıhtılaşmasını sağlayan proteindir."},
        {"soru": "Sıcaklığın SI Birimindeki adı nedir",
          "cevap": "Kelvin",
            "aciklama": "sıcaklık birimi günümzde santigrat olmasına rağmen SI biriminde ki karşılığı kelvin"},
        {"soru": "Hücre zarının dış yüzeyini kaplayan lipitler nelerdir?",
          "cevap": "fosfolipit",
            "aciklama": "Hücre zarı, fosfolipitlerden oluşan bir çift katmandan yapılır."},
        {"soru": "DNA'da bulunan şekerin adı nedir?",
          "cevap": "deoksiriboz",
            "aciklama": "DNA'nın şeker kısmı deoksiribozdan oluşur."},
        {"soru": "Bitkilerde tohumdan yeni bitki gelişimine ne ad verilir?",
          "cevap": "çimlenme",
            "aciklama": "Tohumdan yeni bitki gelişmesi çimlenme olarak adlandırılır."},
        {"soru": "Ağır metal zehirlenmesine yol açan element nedir?",
          "cevap": "kurşun",
            "aciklama": "Kurşun, ağır metal zehirlenmesine yol açabilen bir elementtir."},
        {"soru": "İnsan vücudunda hangi organ oksijen taşır?",
          "cevap": "akciğer",
            "aciklama": "Akciğer, oksijenin vücuda alındığı organdır."},
        {"soru": "İnsan vücudundaki en büyük organ nedir?",
          "cevap": "deri",
            "aciklama": "Deri, insan vücudundaki en büyük organ olarak kabul edilir."},
        {"soru": "Vücudumuzda protein sentezi hangi organelde gerçekleşir?",
          "cevap": "ribozom",
            "aciklama": "Protein sentezi ribozomlarda gerçekleşir."},
        {"soru": "Biyolojik çeşitliliğin temel birimi nedir?",
          "cevap": "birey",
            "aciklama": "Biyolojik çeşitliliğin temel birimi bireydir."},
        {"soru": "Fotosentez hangi organelde gerçekleşir?",
          "cevap": "kloroplast",
            "aciklama": "Fotosentez, kloroplast organelinde gerçekleşir."},
        {"soru": "Kan hücrelerinden hangisi bağışıklık sistemini destekler?",
          "cevap": "akyuvar",
            "aciklama": "Akyuvarlar, bağışıklık sisteminin bir parçasıdır."},
        {"soru": "Yavru gelişimi hangi organel tarafından sağlanır?",
          "cevap": "mitokondri",
            "aciklama": "Mitokondri, hücrede enerji üretir ve yavru gelişimine katkı sağlar."},
        {"soru": "Hangi biyolojik molekül hücre zarını oluşturur?",
          "cevap": "fosfolipit",
            "aciklama": "Hücre zarı, lipit çift katmanından oluşur."},
        {"soru": "Kökenleri farklı fakat işlevleri aynı olan organlara ne ad verilir ... Organ.",
           "cevap": "Analog",
             "aciklama": "Örneğin yarasa kanadı ve kelebek kanadı buna örnek olarak verilebilir."},
        {"soru": "Kökenleri aynı fakat işlevleri farklı olan organlara ne ad verilir ... Organ.",
           "cevap": "Homolog",
             "aciklama": "Örneğin Yarasanın kanadı ve balinanın yüzgeci buna örnek olarak verilebilir."},
        {"soru": "Doğal sınıflandırmalarda kromozoma bakılır mı?",
           "cevap": "Hayır",
             "aciklama": "Doğal sınıflandırmalarda kromozom sayısı canlının bir sınıfsal yapıya ait olduğunu göstermez."},
        {"soru": "Kromozom sayısı canlının gelişmişliğini gösterir mi?",
           "cevap": "Hayır",
             "aciklama": "Eğrelti otunun 500 kromozomu vardır ama sonuç olarak sadece bir ottur :)"},
        {"soru": "Bakteriler aleminde bakteriler kaç hücrelidir",
           "cevap": "Tek",
             "aciklama": "Bakteriler aleminde bakteriler tek hücreli ve prokaryottur."},
        {"soru": "Sınıflandırma basamaklarından en çok çeşit canlı olan basamak hangisidir",
           "cevap": "Alem",
             "aciklama": "Alem Sınıflandırma basamakları piramidinin en alt basamağındadır. "},
        {"soru": "Sınıflandırma basamaklarından en az çeşit canlı olan basamak hangisidir",
           "cevap": "Tür",
             "aciklama": "Tür Sınıflandırma basamakları piramidinin en üst basamağındadır. "},
        {"soru": "Mikroskopla görülemeyen en küçük canlı nedir?",
          "cevap": "virüs",
            "aciklama": "Virüsler mikroskopla görülemeyecek kadar küçüktür."}
        
    ])
]

def quiz_oyunu():
    oyun_yoneticisi = OyunYoneticisi()
     
    # Oyun kurlları oyunun adı yazandırır
    print(" ==== Quick Quiz Oyunu ==== ")
    print(" ..###Her oyuncuya 3 ipucu ve 2 pas hakkı verilir.###.. ")
    print(" ..###Her soruya sadece 1 ipucu hakkı vardır.###.. ")
    print(" ..###Süreniz 100 saniyedir.###.. ")
    print(" ..###Normal sorular 10 puan, ipucu kullanılan sorular 5 puan değerindedir.###.. ")
    print("..### Quick Quizde sayılar yoktur bütün sorular Türkçe karakterlere uygun şekilde cevap verilmelidir.###.. ")
    
    
    #Oyuncu isimleri alınır
    oyuncu1_isim = input("1. oyuncunun adını giriniz: ")
    oyuncu2_isim = input("2. oyuncunun adını giriniz: ")

    #Ouncu nesneleri oluşturulur
    oyuncu1 = Oyuncu(oyuncu1_isim)
    oyuncu2 = Oyuncu(oyuncu2_isim)

    #Oyuncuların sırayla quiiz yapmasını sağlar
    print(f"\n{oyuncu1.isim} için oyun başlıyor!")
    quiz_yap(oyuncu1, kategoriler)
    oyun_raporu_olustur(oyuncu1)


    print(f"\n{oyuncu2.isim} için oyun başlıyor!")
    quiz_yap(oyuncu2, kategoriler)
    oyun_raporu_olustur(oyuncu2)

    #Oyuncuların sonuçları karlıştırılır ve sonuçlar belirlenir
    print("\nOyun bitti! Sonuçlar:")
    print(f"{oyuncu1.isim}: {oyuncu1.puan} puan")
    print(f"{oyuncu2.isim}: {oyuncu2.puan} puan")


    if oyuncu1.puan > oyuncu2.puan:
        print(f"Kazanan: {oyuncu1.isim}!")
        oyun_yoneticisi.yuksek_skoru_kaydet(oyuncu1)
    elif oyuncu2.puan > oyuncu1.puan:
        print(f"Kazanan: {oyuncu2.isim}!")
        oyun_yoneticisi.yuksek_skoru_kaydet(oyuncu2)
    else:
        print("Berabere!")

    #Yüksek skolar listesi yazdırır
    print("\nYüksek Skorlar:")
    for i, skor in enumerate(oyun_yoneticisi.yuksek_skorlar, 1):
        print(f"{i}. {skor['isim']}: {skor['puan']} puan ({skor['tarih']})")

if __name__ == "__main__":
    quiz_oyunu() 
