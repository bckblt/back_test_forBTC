import pandas as pd
import numpy as np
import os

def veriyi_hazirla(dosya_yolu):
    sutunlar = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'c_time', 'q_vol', 'trades', 't_base', 't_quote', 'ignore']
    df = pd.read_csv(dosya_yolu, names=sutunlar, header=None)
    if str(df['open'].iloc[0]).replace('.', '', 1).isdigit() is False:
        df = df.iloc[1:].reset_index(drop=True)
    sayisal = ['open', 'high', 'low', 'close', 'volume']
    df[sayisal] = df[sayisal].apply(pd.to_numeric, errors='coerce')
    df['open_time'] = pd.to_datetime(pd.to_numeric(df['open_time']), unit='ms')
    return df[['open_time', 'open', 'high', 'low', 'close', 'volume']].dropna().reset_index(drop=True)

def indikatorleri_ekle(df):
    df['EMA_200'] = df['close'].rolling(window=200).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['Liq_High'] = df['high'].rolling(window=20).max().shift(1)
    df['Liq_Low'] = df['low'].rolling(window=20).min().shift(1)
    
    df['Sweep_High'] = (df['high'] > df['Liq_High']) & (df['close'] < df['Liq_High']) & (df['close'] < df['EMA_200']) & (df['close'] < df['SMA_50'])
    df['Sweep_Low'] = (df['low'] < df['Liq_Low']) & (df['close'] > df['Liq_Low']) & (df['close'] > df['EMA_200']) & (df['close'] > df['SMA_50'])
    
    return df.dropna().reset_index(drop=True)

def motoru_calistir(df):
    guncel_kasa = 100.0
    baslangic_kasasi = 100.0
    risk_yuzdesi = 0.05
    max_leverage = 10.0    
    fee_rate = 0.0002     
    min_sl_mesafesi = 0.004 
    
    toplam_komisyon = 0.0
    kasa_gecmisi = [guncel_kasa]
    
    istatistikler = {
        "long_kazanc": 0, "long_kayip": 0,
        "short_kazanc": 0, "short_kayip": 0,
        "karlar": [], "zararlar": [],
        "islem_sureleri": [],
        "hata_loglari": []
    }
    
    highs  = df['high'].values
    lows   = df['low'].values
    closes = df['close'].values
    opens  = df['open'].values       # ✅ YENİ: opens dizisi eklendi
    times  = df['open_time'].values
    ema200 = df['EMA_200'].values
    sma50  = df['SMA_50'].values
    
    long_sinyaller  = df.index[df['Sweep_Low']].tolist()
    short_sinyaller = df.index[df['Sweep_High']].tolist()
    tum_sinyaller   = sorted(long_sinyaller + short_sinyaller)
    
    aktif_bitis_idx = -1  # ✅ YENİ: çakışan sinyal önleme
    
    for idx in tum_sinyaller:
        if guncel_kasa <= 0: break
        if idx >= len(df) - 2: break  # ✅ GÜNCELLEME: idx+1 kullanacağız, -2 lazım

        # ✅ YENİ: önceki işlem bitmeden yeni işlem açma
        if idx <= aktif_bitis_idx:
            continue

        # ✅ DÜZELTME: Sinyal mumu kapandıktan sonra, bir sonraki mumun AÇILIŞ fiyatından giriş
        giris_idx    = idx + 1
        giris_fiyati = opens[giris_idx]

        anlik_risk_dolari = guncel_kasa * risk_yuzdesi
        
        if idx in long_sinyaller:
            position  = 'long'
            stop_loss = lows[idx]   # SL hâlâ sinyal mumunun low'u
            if stop_loss >= giris_fiyati: continue
            
            risk_mesafesi = giris_fiyati - stop_loss
            sl_yuzde      = risk_mesafesi / giris_fiyati
            if sl_yuzde < min_sl_mesafesi: continue
                
            take_profit = giris_fiyati + (risk_mesafesi * 2.0)

        else:
            position  = 'short'
            stop_loss = highs[idx]  # SL hâlâ sinyal mumunun high'ı
            if stop_loss <= giris_fiyati: continue
            
            risk_mesafesi = stop_loss - giris_fiyati
            sl_yuzde      = risk_mesafesi / giris_fiyati
            if sl_yuzde < min_sl_mesafesi: continue
                
            take_profit = giris_fiyati - (risk_mesafesi * 2.0)
        
        hesaplanan_buyukluk = anlik_risk_dolari / sl_yuzde
        maksimum_buyukluk   = guncel_kasa * max_leverage
        pozisyon_buyuklugu  = min(hesaplanan_buyukluk, maksimum_buyukluk)
        
        giris_komisyonu = pozisyon_buyuklugu * fee_rate
        toplam_komisyon += giris_komisyonu
        guncel_kasa     -= giris_komisyonu
        
        exit_found = False
        sure       = 0
        kar_zarar  = 0
        
        # ✅ DÜZELTME: Tarama giris_idx+1'den başlıyor (giriş mumunu atla)
        for i in range(giris_idx + 1, len(df)):
            sure     += 1
            curr_high = highs[i]
            curr_low  = lows[i]
            
            if position == 'long':
                if curr_low <= stop_loss:
                    kar_zarar = -(pozisyon_buyuklugu * sl_yuzde)
                    istatistikler["hata_loglari"].append(
                        f"LONG  | Giris: {times[giris_idx]} | SL: {times[i]} | "
                        f"Fiyat: {giris_fiyati:.2f} -> {curr_low:.2f} | "
                        f"EMA200: {ema200[idx]:.2f} | SMA50: {sma50[idx]:.2f}"
                    )
                    exit_found = True
                    aktif_bitis_idx = i  # ✅ YENİ
                    break
                elif curr_high >= take_profit:
                    kar_zarar = pozisyon_buyuklugu * (sl_yuzde * 2.0)
                    exit_found = True
                    aktif_bitis_idx = i  # ✅ YENİ
                    break
            else:
                if curr_high >= stop_loss:
                    kar_zarar = -(pozisyon_buyuklugu * sl_yuzde)
                    istatistikler["hata_loglari"].append(
                        f"SHORT | Giris: {times[giris_idx]} | SL: {times[i]} | "
                        f"Fiyat: {giris_fiyati:.2f} -> {curr_high:.2f} | "
                        f"EMA200: {ema200[idx]:.2f} | SMA50: {sma50[idx]:.2f}"
                    )
                    exit_found = True
                    aktif_bitis_idx = i  # ✅ YENİ
                    break
                elif curr_low <= take_profit:
                    kar_zarar = pozisyon_buyuklugu * (sl_yuzde * 2.0)
                    exit_found = True
                    aktif_bitis_idx = i  # ✅ YENİ
                    break
        
        if exit_found:
            guncel_kasa += kar_zarar
            
            cikis_komisyonu = pozisyon_buyuklugu * fee_rate
            toplam_komisyon += cikis_komisyonu
            guncel_kasa     -= cikis_komisyonu
            
            kasa_gecmisi.append(guncel_kasa)
            istatistikler["islem_sureleri"].append(sure)
            
            if kar_zarar > 0:
                istatistikler["karlar"].append(kar_zarar)
                if position == 'long': istatistikler["long_kazanc"] += 1
                else:                  istatistikler["short_kazanc"] += 1
            else:
                istatistikler["zararlar"].append(kar_zarar)
                if position == 'long': istatistikler["long_kayip"] += 1
                else:                  istatistikler["short_kayip"] += 1

    return istatistikler, baslangic_kasasi, guncel_kasa, toplam_komisyon, kasa_gecmisi

def raporla(istatistikler, baslangic_kasasi, guncel_kasa, toplam_komisyon, kasa_gecmisi):
    toplam_long  = istatistikler["long_kazanc"]  + istatistikler["long_kayip"]
    toplam_short = istatistikler["short_kazanc"] + istatistikler["short_kayip"]
    toplam_islem = toplam_long + toplam_short
    
    long_win_rate  = (istatistikler["long_kazanc"]  / toplam_long  * 100) if toplam_long  > 0 else 0
    short_win_rate = (istatistikler["short_kazanc"] / toplam_short * 100) if toplam_short > 0 else 0
    genel_win_rate = ((istatistikler["long_kazanc"] + istatistikler["short_kazanc"]) / toplam_islem * 100) if toplam_islem > 0 else 0
    
    brut_kar    = sum(istatistikler["karlar"])
    brut_zarar  = abs(sum(istatistikler["zararlar"]))
    profit_factor = (brut_kar / brut_zarar) if brut_zarar > 0 else 0
    
    kasa_serisi  = pd.Series(kasa_gecmisi)
    rolling_max  = kasa_serisi.cummax()
    drawdown     = (kasa_serisi - rolling_max) / rolling_max
    max_drawdown = drawdown.min() * 100
    
    ort_sure       = np.mean(istatistikler["islem_sureleri"]) if istatistikler["islem_sureleri"] else 0
    en_iyi_islem   = max(istatistikler["karlar"])   if istatistikler["karlar"]   else 0
    en_kotu_islem  = min(istatistikler["zararlar"]) if istatistikler["zararlar"] else 0

    with open('summary.txt', 'w') as f:
        f.write("="*50 + "\n")
        f.write("      SMC LIKIDITE AVI - ISTATISTIK RAPORU\n")
        f.write("="*50 + "\n")
        f.write(f"Baslangic Kasasi      : ${baslangic_kasasi:.2f}\n")
        f.write(f"Bitis Kasasi          : ${guncel_kasa:.2f}\n")
        f.write(f"Net Getiri            : %{((guncel_kasa - baslangic_kasasi)/baslangic_kasasi)*100:.2f}\n")
        f.write(f"Odenen Toplam Komisyon: ${toplam_komisyon:.2f}\n")
        f.write(f"Maksimum Drawdown     : %{max_drawdown:.2f}\n")
        f.write("-" * 50 + "\n")
        f.write("      ISLEM PERFORMANSI\n")
        f.write("-" * 50 + "\n")
        f.write(f"Toplam Islem Sayisi   : {toplam_islem}\n")
        f.write(f"Genel Win Rate        : %{genel_win_rate:.2f}\n")
        f.write(f"Profit Factor         : {profit_factor:.2f}\n")
        f.write(f"En Iyi Tekil Islem    : ${en_iyi_islem:.2f}\n")
        f.write(f"En Kotu Tekil Islem   : ${en_kotu_islem:.2f}\n")
        f.write(f"Ort. Islem Suresi     : {ort_sure:.1f} mum\n")
        f.write("-" * 50 + "\n")
        f.write("      LONG / SHORT DAGILIMI\n")
        f.write("-" * 50 + "\n")
        f.write(f"Long Islemler         : {toplam_long} (Win: %{long_win_rate:.2f})\n")
        f.write(f"Short Islemler        : {toplam_short} (Win: %{short_win_rate:.2f})\n")
        f.write("="*50 + "\n")
        f.write("      ZARAR EDILEN ISLEMLER LOG KAYDI\n")
        f.write("="*50 + "\n")
        for log in istatistikler["hata_loglari"]:
            f.write(log + "\n")
    
    # Konsola da yaz
    print("="*50)
    print("      SMC LIKIDITE AVI - ISTATISTIK RAPORU")
    print("="*50)
    print(f"Baslangic Kasasi      : ${baslangic_kasasi:.2f}")
    print(f"Bitis Kasasi          : ${guncel_kasa:.2f}")
    print(f"Net Getiri            : %{((guncel_kasa - baslangic_kasasi)/baslangic_kasasi)*100:.2f}")
    print(f"Odenen Toplam Komisyon: ${toplam_komisyon:.2f}")
    print(f"Maksimum Drawdown     : %{max_drawdown:.2f}")
    print("-" * 50)
    print(f"Toplam Islem Sayisi   : {toplam_islem}")
    print(f"Genel Win Rate        : %{genel_win_rate:.2f}")
    print(f"Profit Factor         : {profit_factor:.2f}")
    print("-" * 50)
    print(f"Long Islemler         : {toplam_long} (Win: %{long_win_rate:.2f})")
    print(f"Short Islemler        : {toplam_short} (Win: %{short_win_rate:.2f})")
    print("="*50)

if __name__ == "__main__":
    dosya = "./btc_1h_data/btc.csv"
    if os.path.exists(dosya):
        df = veriyi_hazirla(dosya)
        df = indikatorleri_ekle(df)
        ist, bas, gun, kom, gec = motoru_calistir(df)
        raporla(ist, bas, gun, kom, gec)
    else:
        print(f"HATA: '{dosya}' bulunamadi.")