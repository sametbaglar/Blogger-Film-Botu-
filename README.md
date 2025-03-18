# Film Botu Kullanım Kılavuzu

Bu bot, Python ve Flask kullanılarak geliştirilmiş, TMDB ve OMDb API’leriyle entegre edilmiş film arama ve paylaşım uygulamasıdır. Bot, film araması yapmanızı, detaylarını görüntülemenizi ve film gönderilerini Blogger hesabınıza e‑posta yoluyla paylaşmanızı sağlar. İşte botun temel kullanım adımları:

## 1. Kurulum ve Hazırlık

- **Gerekli Araçlar:**  
  - Python 3.6 veya üzeri  
  - Flask, Requests, python-dotenv gibi Python kütüphaneleri

- **Kurulum:**  
  - Terminalden gerekli kütüphaneleri yükleyin:  
    ```bash
    pip install flask requests python-dotenv
    ```  
  - Proje dizininde bir **.env** dosyası oluşturun ve TMDB, OMDb API anahtarlarınızı ile e‑posta bilgilerinizi ekleyin.

- **Uygulamayı Başlatma:**  
  - Uygulamanın ana dosyası (örneğin, `app.py`) oluşturulduktan sonra terminalde:
    ```bash
    python app.py
    ```  
  - Uygulama, genellikle [http://127.0.0.1:5000](http://127.0.0.1:5000) adresinde çalışmaya başlayacaktır.

## 2. Botun Kullanımı

- **Film Arama:**  
  Ana sayfada yer alan arama formuna film adını (isteğe bağlı olarak yayın yılı ve tür) girerek film araması yapabilirsiniz. Sonuç listesi, küçük posterler ve çıkış tarihleriyle sunulur.

- **Film Detayları:**  
  Arama sonuçlarından bir filme tıkladığınızda, film detay sayfasına yönlendirilirsiniz. Bu sayfada; film posteri, fragman videosu ve temel film bilgileri görüntülenir.

- **Düzenleyerek Paylaş:** Gönderi ayarlarını düzenleyebileceğiniz bir forma yönlendirir. Bu form sayesinde, film gönderisine dahil edilecek bilgileri (örneğin, açıklama, yönetmen, oyuncular, kategori, çıkış tarihi, film süresi, bütçe, hasılat, TMDB ve IMDb puanları) seçebilir ve ayrıca özel video embed kodu ekleyerek paylaşabilirsiniz.

## 3. Blogger Entegrasyonu

Bot, oluşturduğu SEO uyumlu HTML içeriğini e‑posta yoluyla Blogger hesabınıza gönderir. Gönderi içeriği, tüm öğeleri (poster, fragman, gönderi bilgileri, ek video ve etiketler). E‑postanın sonunda yer alan "Labels:" satırı, TMDB’den çekilen film etiketlerini içerir ve Blogger tarafından gönderi etiketleri olarak atanır.

## Sonuç

Bu film botu sayesinde, film arama, detay görüntüleme ve gönderi paylaşım işlemlerini kolayca gerçekleştirebilirsiniz. Basit yapılandırma seçenekleri ile gönderi içeriğinizi özelleştirebilir, gönderiyi direkt veya düzenleyerek paylaşabilirsiniz. Uygulamayı ihtiyaçlarınıza göre geliştirip, film paylaşım sürecinizi otomatikleştirebilirsiniz.
