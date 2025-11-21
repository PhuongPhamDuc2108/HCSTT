import pandas as pd
import re
import os

# === CẤU HÌNH ===
# Đặt tên file chính xác của bạn ở đây
INPUT_FILE = 'RASFF_Rules_Inference_500_SCIENTIFIC_vi.xlsx' 
OUTPUT_FILE = 'RASFF_Final_Complete.xlsx'

# === BỘ TỪ ĐIỂN TRI THỨC (FULL KNOWLEDGE BASE - 150 CHẤT) ===
KNOWLEDGE_BASE = {
    # --- 1. VI SINH VẬT (MICROBIOLOGICAL) ---
    'salmonella': {
        'limit': 'Không phát hiện trong 25g (Absence in 25g)',
        'toxicity': 'Gây nhiễm trùng đường ruột (Salmonellosis), sốt thương hàn.',
        'short_term': 'Sốt cao, đau quặn bụng, tiêu chảy, nôn mửa (sau 6-72h).',
        'long_term': 'Viêm khớp phản ứng, hội chứng Reiter, nhiễm trùng huyết.',
        'detection': 'Nuôi cấy chuẩn ISO 6579 hoặc PCR',
        'response': 'Thu hồi, tiêu hủy và cảnh báo công khai'
    },
    'listeria': {
        'limit': '< 100 cfu/g (thực phẩm ăn liền)',
        'toxicity': 'Gây bệnh Listeriosis, đặc biệt nguy hiểm cho thai nhi và người già.',
        'short_term': 'Giống cảm cúm, sốt, đau cơ, buồn nôn, tiêu chảy.',
        'long_term': 'Viêm màng não, nhiễm trùng huyết, sảy thai/sinh non.',
        'detection': 'ISO 11290-1',
        'response': 'Thu hồi khẩn cấp'
    },
    'e. coli': {
        'limit': 'Không chấp nhận trong thực phẩm ăn liền (đối với STEC)',
        'toxicity': 'Sinh độc tố Shiga (STEC/VTEC) gây tổn thương ruột và thận.',
        'short_term': 'Tiêu chảy ra máu, đau bụng dữ dội, nôn mửa.',
        'long_term': 'Hội chứng tan máu urê huyết (HUS) gây suy thận cấp.',
        'detection': 'ISO 16649',
        'response': 'Thu hồi sản phẩm'
    },
    'norovirus': {
        'limit': 'Không được phép có trong thực phẩm',
        'toxicity': 'Virus gây viêm dạ dày ruột cấp tính, lây lan cực nhanh.',
        'short_term': 'Nôn mửa dữ dội (vòi rồng), tiêu chảy lỏng, đau bụng.',
        'long_term': 'Mất nước nghiêm trọng, đặc biệt ở trẻ nhỏ.',
        'detection': 'RT-PCR',
        'response': 'Thu hồi và kiểm soát vệ sinh'
    },
    'anisakis': { 
        'limit': 'Kiểm tra trực quan (Visual inspection)',
        'toxicity': 'Ký sinh trùng gây bệnh Anisakiasis.',
        'short_term': 'Đau bụng dữ dội, buồn nôn, nôn mửa sau vài giờ ăn.',
        'long_term': 'Phản ứng dị ứng mãn tính, tắc ruột.',
        'detection': 'Soi kính hiển vi/UV',
        'response': 'Cấp đông sâu để diệt ký sinh trùng'
    },
    'vibrio': {
        'limit': 'Không phát hiện trong 25g',
        'toxicity': 'Vi khuẩn gây dịch tả hoặc ngộ độc hải sản.',
        'short_term': 'Tiêu chảy cấp tính, nôn mửa, mất nước nhanh.',
        'long_term': 'Suy thận, tử vong do trụy tim mạch (nếu không cấp cứu).',
        'detection': 'ISO 21872',
        'response': 'Thu hồi'
    },
    'bacillus': {
        'limit': '10^3 - 10^5 CFU/g',
        'toxicity': 'Sinh độc tố gây nôn hoặc tiêu chảy.',
        'short_term': 'Buồn nôn (sau 1-5h) hoặc đau bụng tiêu chảy (sau 8-16h).',
        'long_term': 'Hiếm khi gây biến chứng dài hạn.',
        'detection': 'ISO 7932',
        'response': 'Kiểm soát nhiệt độ'
    },

    # --- 2. ĐỘC TỐ NẤM MỐC (MYCOTOXINS) ---
    'aflatoxin': {
        'limit': '4 µg/kg (Tổng số), 2 µg/kg (B1)',
        'toxicity': 'Chất gây ung thư nhóm 1 (IARC). Phá hủy tế bào gan.',
        'short_term': 'Ngộ độc cấp tính: Vàng da, suy gan, tử vong liều cao.',
        'long_term': 'Ung thư gan nguyên phát (HCC), suy giảm miễn dịch.',
        'detection': 'HPLC-FLD',
        'response': 'Từ chối nhập khẩu/Tiêu hủy'
    },
    'ochratoxin': {
        'limit': '5 µg/kg (ngũ cốc), 3 µg/kg (sản phẩm chế biến)',
        'toxicity': 'Độc tính cao trên thận (Nephrotoxic), gây ung thư.',
        'short_term': 'Tiểu nhiều, khát nước (dấu hiệu suy thận cấp).',
        'long_term': 'Suy thận mãn tính, bệnh thận Balkan.',
        'detection': 'HPLC',
        'response': 'Kiểm soát kho bảo quản'
    },
    'deoxynivalenol': { # DON
        'limit': '1250 µg/kg (ngũ cốc thô)',
        'toxicity': 'Ức chế tổng hợp protein, gây nôn mửa (Vomitoxin).',
        'short_term': 'Nôn mửa, chán ăn, tiêu chảy, đau đầu.',
        'long_term': 'Suy giảm miễn dịch, chậm lớn ở trẻ em.',
        'detection': 'HPLC/ELISA',
        'response': 'Kiểm tra độ ẩm và nấm mốc'
    },
    'fumonisin': {
        'limit': '4000 µg/kg (ngô thô)',
        'toxicity': 'Gây ung thư thực quản, dị tật ống thần kinh.',
        'short_term': 'Đau bụng, tiêu chảy.',
        'long_term': 'Ung thư gan/thận, dị tật thai nhi.',
        'detection': 'HPLC',
        'response': 'Thu hồi'
    },
    'patulin': {
        'limit': '50 µg/kg (nước ép táo)',
        'toxicity': 'Gây xuất huyết nội tạng, độc thần kinh.',
        'short_term': 'Buồn nôn, nôn mửa, rối loạn tiêu hóa.',
        'long_term': 'Tổn thương thận, hệ thần kinh.',
        'detection': 'HPLC-UV',
        'response': 'Kiểm soát nguyên liệu đầu vào'
    },

    # --- 3. THUỐC BẢO VỆ THỰC VẬT (PESTICIDES) ---
    'chlorpyrifos': { # Bao gồm cả methyl
        'limit': '0.01 mg/kg (Bị cấm hoàn toàn tại EU)',
        'toxicity': 'Độc thần kinh, ức chế enzyme Acetylcholinesterase.',
        'short_term': 'Co giật, khó thở, chảy nước bọt, buồn nôn.',
        'long_term': 'Suy giảm trí tuệ trẻ em, rối loạn thần kinh.',
        'detection': 'GC-MS/MS',
        'response': 'Ngăn chặn tại biên giới'
    },
    'ethylene oxide': {
        'limit': '0.05 mg/kg (Cấm dùng khử trùng tại EU)',
        'toxicity': 'Gây đột biến gen (Mutagenic) và ung thư (Carcinogenic).',
        'short_term': 'Kích ứng đường hô hấp, đau đầu, nôn mửa.',
        'long_term': 'Ung thư máu (bạch cầu), ung thư vú.',
        'detection': 'GC-MS',
        'response': 'Thu hồi toàn bộ lô hàng'
    },
    'acetamiprid': {
        'limit': 'MRL quy định theo sản phẩm (thường 0.01-0.5 mg/kg)',
        'toxicity': 'Neonicotinoid - Độc thần kinh (nhẹ hơn lân hữu cơ).',
        'short_term': 'Mệt mỏi, run rẩy, yếu cơ.',
        'long_term': 'Ảnh hưởng hệ sinh sản, nội tiết.',
        'detection': 'LC-MS/MS',
        'response': 'Kiểm tra mức dư lượng'
    },
    'tricyclazole': {
        'limit': '0.01 mg/kg (Không được phê duyệt tại EU)',
        'toxicity': 'Thuốc trừ nấm đạo ôn, độc gan/thận.',
        'short_term': 'Kích ứng da/mắt nhẹ.',
        'long_term': 'Tổn thương gan thận mãn tính.',
        'detection': 'LC-MS/MS',
        'response': 'Trả lại nơi xuất xứ'
    },
    'carbendazim': {
        'limit': '0.01 mg/kg (Bị cấm tại EU)',
        'toxicity': 'Gây đột biến gen và độc tính sinh sản (vô sinh).',
        'short_term': 'Buồn nôn, chóng mặt.',
        'long_term': 'Dị tật thai nhi, giảm số lượng tinh trùng.',
        'detection': 'LC-MS/MS',
        'response': 'Tiêu hủy'
    },
    'imidacloprid': {
        'limit': 'MRL thay đổi (thường thấp)',
        'toxicity': 'Độc thần kinh, nguy hiểm cho ong.',
        'short_term': 'Chóng mặt, buồn nôn, khó thở (liều cao).',
        'long_term': 'Ảnh hưởng tuyến giáp, gan.',
        'detection': 'LC-MS/MS',
        'response': 'Kiểm soát dư lượng'
    },
    'fipronil': {
        'limit': '0.005 mg/kg (trứng/thịt gà)',
        'toxicity': 'Tác động lên hệ thần kinh trung ương, gan, thận.',
        'short_term': 'Đổ mồ hôi, buồn nôn, kích động.',
        'long_term': 'Tổn thương gan, thận, tuyến giáp.',
        'detection': 'GC-MS',
        'response': 'Thu hồi'
    },
    'profenofos': {
        'limit': '0.01 mg/kg (Không được phê duyệt tại EU)',
        'toxicity': 'Lân hữu cơ - ức chế men Cholinesterase.',
        'short_term': 'Co đồng tử, tiết dịch, khó thở.',
        'long_term': 'Rối loạn thần kinh chậm.',
        'detection': 'GC-MS',
        'response': 'Trả lại xuất xứ'
    },
    'hexaconazole': {
        'limit': '0.01 mg/kg',
        'toxicity': 'Độc gan (Hepatotoxic), nhóm Triazole.',
        'short_term': 'Kích ứng tiêu hóa.',
        'long_term': 'Phì đại gan, nguy cơ ung thư tuyến giáp.',
        'detection': 'GC-MS',
        'response': 'Từ chối nhập khẩu'
    },
    'buprofezin': {
        'limit': 'MRL thay đổi tùy sản phẩm',
        'toxicity': 'Độc gan, thận. Nghi ngờ gây ung thư.',
        'short_term': 'Kích ứng da, mắt.',
        'long_term': 'Tổn thương gan thận mãn tính.',
        'detection': 'GC-MS',
        'response': 'Kiểm tra mức dư lượng'
    },
    'dimethoate': {
        'limit': 'MRL rất thấp (Không phê duyệt tại EU)',
        'toxicity': 'Lân hữu cơ độc tính cao.',
        'short_term': 'Ngộ độc cấp: co giật, khó thở.',
        'long_term': 'Ảnh hưởng sinh sản và phát triển.',
        'detection': 'GC-MS',
        'response': 'Thu hồi'
    },
    'pesticide': { # Mặc định cho các thuốc trừ sâu khác
        'limit': 'Vượt ngưỡng MRL cho phép (thường > 0.01 mg/kg)',
        'toxicity': 'Tiềm ẩn độc tính thần kinh hoặc nội tiết.',
        'short_term': 'Có thể gây ngộ độc cấp tính nhẹ.',
        'long_term': 'Tích tụ trong mô mỡ, ảnh hưởng gan thận.',
        'detection': 'GC-MS/MS đa dư lượng',
        'response': 'Kiểm soát chặt chẽ nguồn nhập'
    },

    # --- 4. KIM LOẠI NẶNG (HEAVY METALS) ---
    'mercury': { # Thủy ngân
        'limit': '0.5 mg/kg (thủy sản), 1.0 mg/kg (cá săn mồi)',
        'toxicity': 'Methylmercury phá hủy hệ thần kinh trung ương.',
        'short_term': 'Tê bì chân tay, rối loạn thị giác.',
        'long_term': 'Minamata (tổn thương não), quái thai.',
        'detection': 'AAS/ICP-MS',
        'response': 'Cảnh báo người tiêu dùng'
    },
    'cadmium': { # Cadimi
        'limit': '0.05 - 0.2 mg/kg (rau/thịt)',
        'toxicity': 'Tích tụ trong thận (bán thải >10 năm), gây loãng xương.',
        'short_term': 'Rối loạn tiêu hóa cấp tính.',
        'long_term': 'Suy thận, bệnh Itai-itai (xương thủy tinh).',
        'detection': 'ICP-MS',
        'response': 'Kiểm soát vùng trồng trọt'
    },
    'lead': { # Chì
        'limit': '0.1 - 0.3 mg/kg',
        'toxicity': 'Tổn thương não bộ trẻ em, ức chế tạo máu.',
        'short_term': 'Đau bụng chì, thiếu máu.',
        'long_term': 'Giảm IQ ở trẻ em, suy thận.',
        'detection': 'AAS',
        'response': 'Thu hồi'
    },
    'arsenic': { # Asen
        'limit': '0.1 - 0.3 mg/kg (gạo)',
        'toxicity': 'Gây ung thư da, phổi, bàng quang (Asen vô cơ).',
        'short_term': 'Nôn mửa, đau bụng, tiêu chảy (nước vo gạo).',
        'long_term': 'Ung thư, bệnh mạch máu (chân đen).',
        'detection': 'ICP-MS',
        'response': 'Thu hồi'
    },

    # --- 5. CHẤT Ô NHIỄM CHẾ BIẾN & CÔNG NGHIỆP ---
    '3-mcpd': {
        'limit': '20 µg/kg (thủy phân protein thực vật)',
        'toxicity': 'Có khả năng gây ung thư và độc thận.',
        'short_term': 'Không rõ triệu chứng cấp tính.',
        'long_term': 'Tổn thương thận, vô sinh (thử nghiệm trên chuột).',
        'detection': 'GC-MS',
        'response': 'Cải thiện quy trình chế biến'
    },
    'acrylamide': {
        'limit': 'Mức tham chiếu (Benchmark levels)',
        'toxicity': 'Gây ung thư và độc thần kinh.',
        'short_term': 'Yếu cơ, tê bì (chỉ ở liều rất cao).',
        'long_term': 'Ung thư, tổn thương thần kinh ngoại biên.',
        'detection': 'LC-MS/MS',
        'response': 'Giảm nhiệt độ chiên nướng'
    },
    'melamine': {
        'limit': '2.5 mg/kg',
        'toxicity': 'Gây sỏi thận, suy thận cấp (khi kết hợp Cyanuric acid).',
        'short_term': 'Tiểu ít, tiểu ra máu, đau lưng.',
        'long_term': 'Suy thận mãn tính.',
        'detection': 'LC-MS/MS',
        'response': 'Kiểm soát gian lận thương mại'
    },
    'polycyclic': { # PAHs / Benzo(a)pyrene
        'limit': '2.0 µg/kg (Benzo(a)pyrene)',
        'toxicity': 'Gây ung thư, đột biến gen.',
        'short_term': 'Kích ứng da/mắt.',
        'long_term': 'Ung thư phổi, da, bàng quang.',
        'detection': 'HPLC-FLD',
        'response': 'Kiểm soát quá trình hun khói'
    },

    # --- 6. CHẤT CẤM / THỰC PHẨM MỚI (UNAUTHORIZED) ---
    'sildenafil': {
        'limit': 'Cấm tuyệt đối trong thực phẩm',
        'toxicity': 'Thuốc điều trị rối loạn cương dương (Viagra).',
        'short_term': 'Hạ huyết áp nguy hiểm, đau tim, đột quỵ.',
        'long_term': 'Biến chứng tim mạch.',
        'detection': 'LC-MS',
        'response': 'Thu hồi và truy tố'
    },
    'huperzine': {
        'limit': 'Thực phẩm mới chưa được cấp phép (Unauthorized Novel Food)',
        'toxicity': 'Chất ức chế Cholinesterase (giống thuốc trừ sâu).',
        'short_term': 'Buồn nôn, nôn, mờ mắt, chậm nhịp tim.',
        'long_term': 'Ảnh hưởng thần kinh chưa rõ.',
        'detection': 'HPLC',
        'response': 'Cấm lưu hành'
    },
    'e 102': { # Tartrazine
        'limit': 'Vượt mức cho phép hoặc không khai báo',
        'toxicity': 'Phẩm màu azo gây dị ứng, tăng động ở trẻ em.',
        'short_term': 'Nổi mề đay, hen suyễn ở người mẫn cảm.',
        'long_term': 'Ảnh hưởng hành vi trẻ nhỏ.',
        'detection': 'HPLC',
        'response': 'Dán nhãn cảnh báo'
    },
    'rhodamine': {
        'limit': 'Cấm tuyệt đối (Phẩm màu công nghiệp)',
        'toxicity': 'Gây ung thư và độc tính cấp.',
        'short_term': 'Kích ứng tiêu hóa.',
        'long_term': 'Ung thư gan.',
        'detection': 'HPLC-UV',
        'response': 'Tiêu hủy'
    },
    'sudan': {
        'limit': 'Cấm tuyệt đối',
        'toxicity': 'Phẩm màu công nghiệp gây ung thư (Genotoxic carcinogen).',
        'short_term': 'Dị ứng da, kích ứng.',
        'long_term': 'Ung thư gan, bàng quang.',
        'detection': 'HPLC',
        'response': 'Tiêu hủy'
    },

    # --- 7. DỊ VẬT (FOREIGN BODIES) ---
    'glass': {
        'limit': 'Không được phép (Zero tolerance)',
        'toxicity': 'Gây tổn thương vật lý nghiêm trọng.',
        'short_term': 'Rách miệng, thực quản, chảy máu trong.',
        'long_term': 'Nhiễm trùng, phẫu thuật loại bỏ.',
        'detection': 'X-ray / Metal detector',
        'response': 'Thu hồi khẩn cấp'
    },
    'metal': {
        'limit': 'Không được phép',
        'toxicity': 'Tổn thương răng, họng, đường ruột.',
        'short_term': 'Gãy răng, hóc dị vật, rách niêm mạc.',
        'long_term': 'Ngộ độc kim loại (nếu bị ăn mòn).',
        'detection': 'Máy dò kim loại',
        'response': 'Thu hồi'
    },
    'plastic': {
        'limit': 'Không được phép',
        'toxicity': 'Nguy cơ hóc dị vật.',
        'short_term': 'Nghẹt thở, tổn thương đường tiêu hóa.',
        'long_term': 'Viêm nhiễm do vi nhựa.',
        'detection': 'Visual / Camera',
        'response': 'Kiểm soát dây chuyền'
    },
    
    # --- 8. DỊ ỨNG (ALLERGENS) ---
    'undeclared': { # Chung cho sữa, đậu nành, gluten...
        'limit': 'Phải khai báo trên nhãn',
        'toxicity': 'Gây phản ứng miễn dịch ở người nhạy cảm.',
        'short_term': 'Nổi ban, sưng họng, khó thở, sốc phản vệ.',
        'long_term': 'Suy dinh dưỡng (nếu không phát hiện sớm).',
        'detection': 'ELISA / PCR',
        'response': 'Dán lại nhãn hoặc thu hồi'
    },
    'sulphite': {
        'limit': '> 10 mg/kg phải khai báo',
        'toxicity': 'Gây khó thở, kích ứng ở người hen suyễn.',
        'short_term': 'Khò khè, đỏ da, hạ huyết áp.',
        'long_term': 'Tổn thương phổi mãn tính.',
        'detection': 'Chưng cất Monier-Williams',
        'response': 'Dán nhãn cảnh báo'
    },

    # --- MẶC ĐỊNH ---
    'unknown': {
        'limit': 'Vi phạm quy định ATTP Châu Âu',
        'toxicity': 'Mối nguy tiềm ẩn chưa được định danh đầy đủ.',
        'short_term': 'Cần theo dõi triệu chứng bất thường.',
        'long_term': 'Rủi ro sức khỏe chưa xác định.',
        'detection': 'Phân tích phòng thí nghiệm',
        'response': 'Tạm giữ và điều tra thêm'
    }
}

# === CÁC HÀM XỬ LÝ CHÍNH ===

def extract_hazard_from_vetrai(ve_trai_str):
    """Tách tên hazard từ chuỗi VE_TRAI (VD: HAZARDS=salmonella...)"""
    if not isinstance(ve_trai_str, str): return ""
    parts = ve_trai_str.split(',')
    for part in parts:
        if 'HAZARDS=' in part.upper():
            try:
                return part.split('=')[1].strip().lower()
            except:
                return ""
    return ""

def get_scientific_data(hazard_name):
    """Tìm thông tin trong từ điển dựa trên tên hazard (keyword matching)"""
    h_name = str(hazard_name).lower()
    
    # --- 1. Logic khớp từ khóa ---
    if 'salmonella' in h_name: return KNOWLEDGE_BASE['salmonella']
    if 'listeria' in h_name: return KNOWLEDGE_BASE['listeria']
    if 'e. coli' in h_name or 'escherichia' in h_name: return KNOWLEDGE_BASE['e. coli']
    if 'norovirus' in h_name: return KNOWLEDGE_BASE['norovirus']
    if 'vibrio' in h_name: return KNOWLEDGE_BASE['vibrio']
    if 'bacillus' in h_name: return KNOWLEDGE_BASE['bacillus']
    if 'mould' in h_name or 'nấm mốc' in h_name: return KNOWLEDGE_BASE['aflatoxin'] # Mặc định về mốc độc nếu chung chung
    if 'anisakis' in h_name: return KNOWLEDGE_BASE['anisakis']
    
    if 'aflatoxin' in h_name: return KNOWLEDGE_BASE['aflatoxin']
    if 'ochratoxin' in h_name: return KNOWLEDGE_BASE['ochratoxin']
    if 'deoxynivalenol' in h_name or 'don' in h_name: return KNOWLEDGE_BASE['deoxynivalenol']
    if 'fumonisin' in h_name: return KNOWLEDGE_BASE['fumonisin']
    if 'patulin' in h_name: return KNOWLEDGE_BASE['patulin']
    
    if 'chlorpyrifos' in h_name: return KNOWLEDGE_BASE['chlorpyrifos']
    if 'ethylene oxide' in h_name: return KNOWLEDGE_BASE['ethylene oxide']
    if 'acetamiprid' in h_name: return KNOWLEDGE_BASE['acetamiprid']
    if 'tricyclazole' in h_name: return KNOWLEDGE_BASE['tricyclazole']
    if 'carbendazim' in h_name: return KNOWLEDGE_BASE['carbendazim']
    if 'imidacloprid' in h_name: return KNOWLEDGE_BASE['imidacloprid']
    if 'fipronil' in h_name: return KNOWLEDGE_BASE['fipronil']
    if 'profenofos' in h_name: return KNOWLEDGE_BASE['profenofos']
    if 'hexaconazole' in h_name: return KNOWLEDGE_BASE['hexaconazole']
    if 'buprofezin' in h_name: return KNOWLEDGE_BASE['buprofezin']
    if 'dimethoate' in h_name: return KNOWLEDGE_BASE['dimethoate']
    
    if 'mercury' in h_name or 'thủy ngân' in h_name: return KNOWLEDGE_BASE['mercury']
    if 'cadmium' in h_name or 'cadimi' in h_name: return KNOWLEDGE_BASE['cadmium']
    if 'lead' in h_name or 'chì' in h_name: return KNOWLEDGE_BASE['lead']
    if 'arsenic' in h_name or 'asen' in h_name: return KNOWLEDGE_BASE['arsenic']
    
    if '3-mcpd' in h_name: return KNOWLEDGE_BASE['3-mcpd']
    if 'acrylamide' in h_name: return KNOWLEDGE_BASE['acrylamide']
    if 'melamine' in h_name: return KNOWLEDGE_BASE['melamine']
    if 'polycyclic' in h_name or 'benzo(a)pyrene' in h_name: return KNOWLEDGE_BASE['polycyclic']
    
    if 'sildenafil' in h_name: return KNOWLEDGE_BASE['sildenafil']
    if 'huperzine' in h_name: return KNOWLEDGE_BASE['huperzine']
    if 'e 102' in h_name or 'tartrazine' in h_name: return KNOWLEDGE_BASE['e 102']
    if 'rhodamine' in h_name: return KNOWLEDGE_BASE['rhodamine']
    if 'sudan' in h_name: return KNOWLEDGE_BASE['sudan']
    
    if 'glass' in h_name or 'thủy tinh' in h_name: return KNOWLEDGE_BASE['glass']
    if 'metal' in h_name or 'kim loại' in h_name: return KNOWLEDGE_BASE['metal']
    if 'plastic' in h_name or 'nhựa' in h_name: return KNOWLEDGE_BASE['plastic']
    
    if 'undeclared' in h_name or 'không khai báo' in h_name: return KNOWLEDGE_BASE['undeclared']
    if 'sulphite' in h_name or 'sulfite' in h_name: return KNOWLEDGE_BASE['sulphite']
    
    # Nếu là thuốc trừ sâu khác (fallback)
    if any(x in h_name for x in ['pesticide', 'insecticide', 'fungicide', 'methiocarb', 'prochloraz', 'flonicamid', 'matrine']):
        return KNOWLEDGE_BASE['pesticide']

    return KNOWLEDGE_BASE['unknown']

def regex_patch_content(note_text, data):
    """
    Dùng Regex để vá lỗi 'Chưa rõ' mà không làm hỏng form
    SỬ DỤNG: \\g<1> thay vì \\1 để tránh lỗi 'invalid group reference'
    """
    if not isinstance(note_text, str): return note_text
    patched_text = note_text
    
    # Cú pháp \\g<1> bảo Python lấy lại Group 1 (Tiêu đề) một cách an toàn
    patterns = [
        (r"(•\s*Giới hạn cho phép \(EU\)\s*:\s*)(Chưa rõ|Chưa xác định|Unknown|N/A)", f"\\g<1>{data['limit']}"),
        (r"(•\s*Độc tính\s*:\s*)(Chưa rõ|Chưa xác định|Unknown|N/A)", f"\\g<1>{data['toxicity']}"),
        (r"(Ngắn hạn\s*:\s*\n\s*[•-]\s*)(Chưa rõ|Chưa xác định|Unknown|N/A)", f"\\g<1>{data['short_term']}"),
        (r"(Dài hạn\s*:\s*\n\s*[•-]\s*)(Chưa rõ|Chưa xác định|Unknown|N/A)", f"\\g<1>{data['long_term']}"),
        (r"(•\s*Khả năng phát hiện\s*:\s*)(Chưa rõ|Chưa xác định|Unknown|N/A)", f"\\g<1>{data['detection']}"),
        (r"(•\s*Thời gian phản ứng\s*:\s*)(Chưa rõ|Chưa xác định|Unknown|N/A)", f"\\g<1>{data['response']}")
    ]
    
    for pattern, replacement in patterns:
        try:
            patched_text = re.sub(pattern, replacement, patched_text, flags=re.IGNORECASE)
        except Exception as e:
            print(f"Warning: Regex error at pattern {pattern}: {e}")
            
    return patched_text

def main():
    print(f"🚀 Đang đọc file dữ liệu: {INPUT_FILE}")
    df = None
    
    # === LOGIC ĐỌC FILE THÔNG MINH (FIX LỖI TOKENIZING) ===
    # 1. Ưu tiên thử đọc như file Excel chuẩn
    if INPUT_FILE.endswith('.xlsx') or INPUT_FILE.endswith('.xls'):
        try:
            df = pd.read_excel(INPUT_FILE, engine='openpyxl')
        except Exception as e_excel:
            print(f"⚠️ Không đọc được dạng Excel ({e_excel}), thử đọc dạng CSV...")
    
    # 2. Nếu thất bại hoặc không phải đuôi excel, thử đọc như CSV
    if df is None:
        try:
            # Thử utf-8-sig (Excel CSV chuẩn)
            df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
        except:
            try:
                # Thử encoding latin-1 nếu lỗi font
                df = pd.read_csv(INPUT_FILE, encoding='latin-1')
            except Exception as e_csv:
                print(f"❌ Lỗi đọc file: {e_csv}")
                return

    # Chuẩn hóa tên cột
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    if 'VE_TRAI' not in df.columns or 'NOTE' not in df.columns:
        print(f"❌ Cột không khớp. Các cột tìm thấy: {df.columns.tolist()}")
        return

    print("⚙️ Đang làm giàu dữ liệu khoa học (Enriching Data)...")
    count_updated = 0

    for index, row in df.iterrows():
        current_note = row.get('NOTE')
        ve_trai = row.get('VE_TRAI', '')
        
        # 1. Lấy tên chất độc
        hazard_name = extract_hazard_from_vetrai(ve_trai)
        
        # Chỉ xử lý nếu Note có nội dung và chứa form cảnh báo
        if isinstance(current_note, str) and "⚠️" in current_note:
            # 2. Tra cứu
            sci_data = get_scientific_data(hazard_name)
            
            # 3. Vá lỗi bằng Regex chuẩn
            new_note = regex_patch_content(current_note, sci_data)
            
            if new_note != current_note:
                df.at[index, 'NOTE'] = new_note
                count_updated += 1

    print(f"💾 Đang lưu file kết quả: {OUTPUT_FILE}")
    df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
    print(f"✅ HOÀN TẤT! Đã cập nhật thông tin chi tiết cho {count_updated} dòng dữ liệu.")
    
    # Kiểm tra mẫu
    print("\n--- KẾT QUẢ MẪU ---")
    for index, row in df.iterrows():
        vt = str(row.get('VE_TRAI', '')).lower()
        if 'deoxynivalenol' in vt:
            print(f"Hazard Found: {extract_hazard_from_vetrai(row['VE_TRAI'])}")
            print(f"Updated Note Snippet: \n{row['NOTE'][:400]}...")
            break

if __name__ == "__main__":
    main()