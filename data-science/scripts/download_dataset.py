import os
import sys

def check_dependencies():
    """Memeriksa apakah library yang dibutuhkan sudah terinstall."""
    missing_libs = []
    try:
        import datasets
    except ImportError:
        missing_libs.append("datasets")
    
    try:
        import pandas
    except ImportError:
        missing_libs.append("pandas")
        
    if missing_libs:
        print("[!] Library berikut belum terinstall:")
        for lib in missing_libs:
            print(f"    - {lib}")
        print("\nSilakan jalankan perintah berikut untuk menginstall:")
        print("pip install datasets pandas\n")
        return False
    return True

def main():
    if not check_dependencies():
        sys.exit(1)
        
    from datasets import load_dataset
    import pandas as pd
    
    # Path output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_dir = os.path.join(script_dir, "..", "datasets")
    os.makedirs(datasets_dir, exist_ok=True)
    
    print("[*] Memulai download dataset 'datasetmaster/resumes' dari Hugging Face...")
    try:
        # Load dataset dari Hugging Face
        # Dataset ini sangat bagus untuk Resume Parsing (memiliki JSON terstruktur)
        dataset = load_dataset("datasetmaster/resumes")
        
        # Ambil bagian 'train'
        train_data = dataset['train']
        
        # Konversi ke pandas DataFrame
        df = pd.DataFrame(train_data)
        
        # Menyimpan ke CSV
        csv_path = os.path.join(datasets_dir, "resume_dataset_parsed.csv")
        df.to_csv(csv_path, index=False)
        print(f"[+] Berhasil mengunduh dan menyimpan dataset ke: {csv_path}")
        print(f"    Total data: {len(df)} resume.")
        
    except Exception as e:
        print(f"[x] Terjadi kesalahan saat mendownload dataset: {e}")
        print("\nAlternatif: Anda bisa mengunjungi link berikut untuk download langsung:")
        print("https://huggingface.co/datasets/datasetmaster/resumes")

if __name__ == "__main__":
    main()
