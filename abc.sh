#!/bin/bash

# Yapılandırma Ayarları
SYMBOL="BTCUSDT"
INTERVAL="1h"
YEARS=("2024" "2025")
MONTHS=("01" "02" "03" "04" "05" "06" "07" "08" "09" "10" "11" "12")
BASE_URL="https://data.binance.vision/data/spot/monthly/klines"
DIR_NAME="btc_1h_data"
OUTPUT_FILE="${SYMBOL}-${INTERVAL}-all.csv"

# Verilerin tutulacağı klasörü oluştur ve içine gir
mkdir -p "$DIR_NAME"
cd "$DIR_NAME" || exit

echo "Binance üzerinden $SYMBOL $INTERVAL verileri çekiliyor..."
echo "--------------------------------------------------"

# Hedef dosyayı sıfırla (eğer önceden varsa üzerine yazmasın diye)
> "$OUTPUT_FILE"

# Yıllar ve aylar üzerinde dönerek işlemleri sırayla yap
for year in "${YEARS[@]}"; do
    for month in "${MONTHS[@]}"; do
        ZIP_NAME="${SYMBOL}-${INTERVAL}-${year}-${month}.zip"
        CSV_NAME="${SYMBOL}-${INTERVAL}-${year}-${month}.csv"
        URL="${BASE_URL}/${SYMBOL}/${INTERVAL}/${ZIP_NAME}"
        
        # 1. Adım: İndir
        wget -q -c "$URL"
        
        # Eğer indirme başarılıysa (dosya varsa) diğer adımlara geç
        # Not: Henüz yaşanmamış aylar için (örn. 2025 sonu) wget hata vermez ama dosya inmez, bu if bloğu o durumu yönetir.
        if [ -f "$ZIP_NAME" ]; then
            echo "$year-$month indirildi, birleştiriliyor..."
            
            # 2. Adım: Zip'ten çıkar ve zip'i sil
            unzip -q -o "$ZIP_NAME"
            rm "$ZIP_NAME"
            
            # 3. Adım: Çıkan CSV'yi ana dosyaya ekle ve ham CSV'yi sil
            if [ -f "$CSV_NAME" ]; then
                cat "$CSV_NAME" >> "$OUTPUT_FILE"
                rm "$CSV_NAME"
            fi
        fi
    done
done

echo "--------------------------------------------------"
echo "İşlem başarıyla tamamlandı!"
echo "Tüm veriler '$DIR_NAME/$OUTPUT_FILE' konumunda tek bir dosyada birleştirildi."