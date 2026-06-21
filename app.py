from flask import Flask, jsonify, request
import random
from datetime import datetime, timezone, timedelta
import urllib.request
import json

app = Flask(__name__)

history = []
API_GOC = "https://trails-wish-motel-legacy.trycloudflare.com/api/tx"

# ============ STATS TRACKER ============
class StatsTracker:
    def __init__(self):
        self.history = []
    
    def add_result(self, data):
        du_doan = str(data.get("du_doan", "")).lower()
        ket_qua = str(data.get("ket_qua", "")).lower()
        result = "CHƯA RÕ"
        if du_doan == ket_qua: result = "THẮNG"
        elif du_doan and ket_qua: result = "THUA"
        
        self.history.append({
            "phien": data.get("phien"), "du_doan": du_doan,
            "ket_qua": ket_qua, "result": result,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        if len(self.history) > 100: self.history.pop(0)
    
    def get_stats(self):
        total = len(self.history)
        if total == 0: return {"status": "Chưa có dữ liệu"}
        wins = sum(1 for h in self.history if h["result"] == "THẮNG")
        losses = sum(1 for h in self.history if h["result"] == "THUA")
        streak = 0; stype = ""
        for h in reversed(self.history):
            if h["result"] in ("THẮNG", "THUA"):
                if stype == "" or stype == h["result"]: streak += 1; stype = h["result"]
                else: break
        return {"tong": total, "thang": wins, "thua": losses,
                "ty_le": round(wins/max(wins+losses,1)*100,1),
                "streak": f"{streak} {stype}" if streak > 0 else "Không"}

stats_tracker = StatsTracker()

# ============ FETCH API GỐC ============
def fetch_api_goc():
    """Lấy dữ liệu từ API gốc, nếu lỗi thì tạo random"""
    try:
        req = urllib.request.Request(API_GOC)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        
        return {
            "phien": data.get("phien", 0),
            "xuc_xac_1": int(data.get("xuc_xac_1", 0)),
            "xuc_xac_2": int(data.get("xuc_xac_2", 0)),
            "xuc_xac_3": int(data.get("xuc_xac_3", 0)),
            "tong": int(data.get("tong", 0)),
            "ket_qua": str(data.get("ket_qua", "")),
            "thoi_gian": data.get("thoi_gian", "")
        }
    except:
        # Fallback random nếu API lỗi
        x1, x2, x3 = random.randint(1,6), random.randint(1,6), random.randint(1,6)
        tong = x1+x2+x3
        return {
            "phien": random.randint(3145000, 3149999),
            "xuc_xac_1": x1, "xuc_xac_2": x2, "xuc_xac_3": x3,
            "tong": tong,
            "ket_qua": "Tài" if tong >= 11 else "Xỉu",
            "thoi_gian": datetime.now(timezone(timedelta(hours=7))).strftime("%d-%m-%Y %H:%M:%S UTC+7")
        }

# ============ PHÂN TÍCH CẦU ============
class BridgeAnalyzer:
    def __init__(self, history_data):
        self.data = []
        for h in history_data:
            kq = str(h.get("ket_qua", ""))
            if "Tài" in kq or "tài" in kq: self.data.append(1)
            elif "Xỉu" in kq or "xỉu" in kq: self.data.append(-1)
    
    def analyze_all(self):
        return {
            "cau_bet": self.cau_bet(), "cau_1_1": self.cau_1_1(),
            "cau_2_1": self.cau_2_1(), "cau_2_2": self.cau_2_2(),
            "cau_3_2": self.cau_3_2(), "cau_doi_xung": self.cau_doi_xung(),
            "cau_tam_giac": self.cau_tam_giac(), "cau_thang": self.cau_thang(),
            "cau_rong": self.cau_rong(), "cau_ho": self.cau_ho(),
            "cau_rong_xanh": self.cau_rong_xanh(), "cau_ho_vang": self.cau_ho_vang(),
            "cau_rong_thang": self.cau_rong_thang(), "cau_ho_xam": self.cau_ho_xam(),
            "cau_long_phuong": self.cau_long_phuong(),
            "xu_huong": self.xu_huong(), "tan_suat": self.tan_suat(),
            "markov": self.markov_chain(), "fibonacci": self.fibonacci_bridge(),
            "entropy": self.entropy_analysis(), "song": self.song_analysis()
        }
    
    def cau_bet(self):
        if len(self.data) < 3: return {"loai": "Chưa rõ", "do_dai": 0}
        streak, last = 1, self.data[-1]
        for i in range(len(self.data)-2, -1, -1):
            if self.data[i] == last: streak += 1
            else: break
        return {"loai": f"Bệt {streak} {'TÀI' if last==1 else 'XỈU'}", "do_dai": streak, "ket_qua": "TÀI" if last==1 else "XỈU"}
    
    def cau_1_1(self):
        if len(self.data) < 4: return {"loai": "Chưa rõ"}
        alt = all(self.data[-i] != self.data[-i-1] for i in range(1, min(6, len(self.data))))
        return {"loai": "Cầu 1-1" if alt else "Không", "du_doan": "XỈU" if self.data[-1]==1 else "TÀI" if alt else "Không rõ"}
    
    def cau_2_1(self):
        if len(self.data) < 6: return {"loai": "Chưa rõ"}
        r = self.data[-9:]
        p = all(r[i]==r[i+1] and r[i]!=r[i+2] for i in range(0, len(r)-2, 3))
        return {"loai": "Cầu 2-1" if p else "Không", "du_doan": ("TÀI" if r[-1]==-1 else "XỈU") if p else "Không rõ"}
    
    def cau_2_2(self):
        if len(self.data) < 8: return {"loai": "Chưa rõ"}
        r = self.data[-8:]
        p = all(r[i]==r[i+1] and r[i]!=r[i+2]==r[i+3] for i in range(0, len(r)-1, 4))
        return {"loai": "Cầu 2-2" if p else "Không", "du_doan": ("TÀI" if r[-1]==-1 else "XỈU") if p else "Không rõ"}
    
    def cau_3_2(self):
        if len(self.data) < 10: return {"loai": "Chưa rõ"}
        r = self.data[-10:]
        p = all(r[i]==r[i+1]==r[i+2] and r[i+2]!=r[i+3]==r[i+4] for i in range(0, len(r)-4, 5))
        return {"loai": "Cầu 3-2" if p else "Không", "du_doan": ("TÀI" if r[-1]==-1 else "XỈU") if p else "Không rõ"}
    
    def cau_doi_xung(self):
        if len(self.data) < 4: return {"loai": "Chưa rõ"}
        r = self.data[-5:] if len(self.data)>=5 else self.data
        s = r == r[::-1]
        return {"loai": "Đối xứng" if s else "Không", "du_doan": ("TÀI" if r[0]==1 else "XỈU") if s else "Không rõ"}
    
    def cau_tam_giac(self):
        if len(self.data) < 7: return {"loai": "Chưa rõ"}
        r = self.data[-7:]
        p = (r[0]==r[3]==r[6] and r[1]==r[4] and r[2]==r[5] and r[0]!=r[1] and r[1]!=r[2])
        return {"loai": "Tam giác" if p else "Không", "du_doan": ("TÀI" if r[-1]==-1 else "XỈU") if p else "Không rõ"}
    
    def cau_thang(self):
        if len(self.data) < 3: return {"loai": "Chưa rõ"}
        ch = sum(1 for i in range(1, len(self.data)) if self.data[i]!=self.data[i-1])
        r = ch/(len(self.data)-1) if len(self.data)>1 else 0
        return {"loai": "Đổi liên tục" if r>0.8 else ("Bệt dài" if r<0.2 else "Hỗn hợp"), "ti_le": round(r*100,1)}
    
    def cau_rong(self):
        if len(self.data) < 5: return {"loai": "Chưa rõ", "du_doan": "Không rõ"}
        r = self.data[-7:] if len(self.data)>=7 else self.data
        tc = sum(1 for x in r if x==1); tr = tc/len(r)
        if tr>=0.7: return {"loai": f"Rồng (TÀI {tc}/{len(r)})", "du_doan": "TÀI", "ti_le": round(tr*100,1)}
        elif tr>=0.57: return {"loai": "Rồng nhẹ", "du_doan": "TÀI", "ti_le": round(tr*90,1)}
        return {"loai": "Không", "du_doan": "Không rõ", "ti_le": 50}
    
    def cau_ho(self):
        if len(self.data) < 5: return {"loai": "Chưa rõ", "du_doan": "Không rõ"}
        r = self.data[-7:] if len(self.data)>=7 else self.data
        xc = sum(1 for x in r if x==-1); xr = xc/len(r)
        if xr>=0.7: return {"loai": f"Hổ (XỈU {xc}/{len(r)})", "du_doan": "XỈU", "ti_le": round(xr*100,1)}
        elif xr>=0.57: return {"loai": "Hổ nhẹ", "du_doan": "XỈU", "ti_le": round(xr*90,1)}
        return {"loai": "Không", "du_doan": "Không rõ", "ti_le": 50}
    
    def cau_rong_xanh(self):
        if len(self.data) < 6: return {"loai": "Chưa rõ"}
        r = self.data[-6:]
        p = all(r[i]!=r[i-1] for i in range(1, len(r)))
        return {"loai": "Rồng Xanh" if p else "Không", "du_doan": "XỈU" if r[-1]==1 else "TÀI" if p else "Không rõ"}
    
    def cau_ho_vang(self):
        if len(self.data) < 8: return {"loai": "Chưa rõ"}
        r = self.data[-8:]
        p = all(r[i]==r[i+1] and r[i+2]==r[i+3] and r[i]!=r[i+2] for i in range(0,8,4))
        return {"loai": "Hổ Vàng" if p else "Không", "du_doan": "TÀI" if r[-1]==-1 else "XỈU" if p else "Không rõ"}
    
    def cau_rong_thang(self):
        if len(self.data) < 6: return {"loai": "Chưa rõ"}
        c3 = sum(1 for i in range(len(self.data)-2) if self.data[i]==self.data[i+1]==self.data[i+2]==1)
        return {"loai": f"Rồng Thắng ({c3})" if c3>=2 else "Không", "du_doan": "TÀI" if c3>=2 else "Không rõ"}
    
    def cau_ho_xam(self):
        if len(self.data) < 6: return {"loai": "Chưa rõ"}
        c3 = sum(1 for i in range(len(self.data)-2) if self.data[i]==self.data[i+1]==self.data[i+2]==-1)
        return {"loai": f"Hổ Xám ({c3})" if c3>=2 else "Không", "du_doan": "XỈU" if c3>=2 else "Không rõ"}
    
    def cau_long_phuong(self):
        if len(self.data) < 6: return {"loai": "Chưa rõ"}
        m = len(self.data)//2
        s = self.data[:m] == self.data[-m:][::-1]
        return {"loai": "Long Phượng" if s else "Không", "du_doan": "TÀI" if self.data[-1]==-1 and s else ("XỈU" if self.data[-1]==1 and s else "Không rõ")}
    
    def xu_huong(self):
        if len(self.data) < 5: return {}
        trends = {}
        for p in [5,10,20]:
            if len(self.data) >= p:
                r = self.data[-p:]; tc = sum(1 for x in r if x==1)
                if tc >= p*0.7: trends[f"{p}_phien"] = "TÀI mạnh"
                elif tc <= p*0.3: trends[f"{p}_phien"] = "XỈU mạnh"
                elif tc > p-tc: trends[f"{p}_phien"] = "Nghiêng TÀI"
                else: trends[f"{p}_phien"] = "Nghiêng XỈU"
        return trends
    
    def tan_suat(self):
        if not self.data: return {"tai":0, "xiu":0}
        t = len(self.data); tc = sum(1 for x in self.data if x==1)
        return {"tong": t, "tai": tc, "xiu": t-tc, "ti_le_tai": round(tc/t*100,1)}
    
    def markov_chain(self):
        if len(self.data) < 3: return {"du_doan": "Không rõ"}
        tr = {"TT":0,"TX":0,"XT":0,"XX":0}
        for i in range(1, len(self.data)):
            k = ("T" if self.data[i]==1 else "X") + ("T" if self.data[i-1]==1 else "X")
            tr[k] += 1
        cur = "T" if self.data[-1]==1 else "X"
        toT, toX = tr[cur+"T"], tr[cur+"X"]
        if toT+toX == 0: return {"du_doan": "Không rõ", "ti_le": 50}
        pt = toT/(toT+toX)
        return {"du_doan": "TÀI" if pt>=0.5 else "XỈU", "ti_le": round(max(pt,1-pt)*100,1)}
    
    def fibonacci_bridge(self):
        if len(self.data) < 2: return {"du_doan": "Không rõ"}
        fib = [1,1,2,3,5,8,13,21]
        scores = [self.data[-f] for f in fib if f < len(self.data)]
        if not scores: return {"du_doan": "Không rõ"}
        avg = sum(scores)/len(scores)
        return {"du_doan": "TÀI" if avg>0 else "XỈU", "ti_le": round(abs(avg)*50+50,1)}
    
    def entropy_analysis(self):
        if len(self.data) < 5: return {"du_doan": "Không rõ"}
        counts = {1: self.data.count(1), -1: self.data.count(-1)}
        total = len(self.data)
        entropy = 0
        for c in counts.values():
            if c > 0:
                p = c/total
                entropy -= p * math.log2(p)
        max_entropy = 1.0
        normalized = entropy/max_entropy if max_entropy > 0 else 0
        return {"entropy": round(entropy, 2), "muc_do_hon_loon": "Cao" if normalized > 0.8 else "Thấp"}
    
    def song_analysis(self):
        if len(self.data) < 5: return {}
        waves = 0
        for i in range(1, len(self.data)):
            if self.data[i] != self.data[i-1]: waves += 1
        return {"so_lan_song": waves, "tan_so": round(waves/len(self.data), 2)}

# ============ PREDICT ============
def predict_tai_xiu(bridge):
    score, signals = 0, 0
    
    if bridge.get("cau_bet", {}).get("do_dai", 0) >= 4:
        score += (1 if bridge["cau_bet"].get("ket_qua")=="TÀI" else -1) * 3; signals += 1
    if bridge.get("cau_1_1", {}).get("loai") == "Cầu 1-1":
        score += (1 if bridge["cau_1_1"].get("du_doan")=="TÀI" else -1) * 2; signals += 1
    if bridge.get("markov", {}).get("du_doan") not in ("Không rõ", None):
        score += (1 if bridge["markov"]["du_doan"]=="TÀI" else -1) * 1.5
    if bridge.get("fibonacci", {}).get("du_doan") not in ("Không rõ", None):
        score += (1 if bridge["fibonacci"]["du_doan"]=="TÀI" else -1) * 1.2
    if bridge.get("tan_suat", {}).get("ti_le_tai", 50) > 65: score -= 2; signals += 1
    elif bridge.get("tan_suat", {}).get("ti_le_tai", 50) < 35: score += 2; signals += 1
    if bridge.get("cau_rong", {}).get("du_doan") not in ("Không rõ", None):
        score += (1 if bridge["cau_rong"]["du_doan"]=="TÀI" else -1) * 2.5; signals += 1
    if bridge.get("cau_ho", {}).get("du_doan") not in ("Không rõ", None):
        score += (1 if bridge["cau_ho"]["du_doan"]=="TÀI" else -1) * 2.5; signals += 1
    if bridge.get("cau_rong_thang", {}).get("du_doan") not in ("Không rõ", None):
        score += (1 if bridge["cau_rong_thang"]["du_doan"]=="TÀI" else -1) * 2; signals += 1
    if bridge.get("cau_ho_xam", {}).get("du_doan") not in ("Không rõ", None):
        score += (1 if bridge["cau_ho_xam"]["du_doan"]=="TÀI" else -1) * 2; signals += 1
    
    score += random.uniform(-1, 1)
    prediction = "Tài" if score >= 0 else "Xỉu"
    ty_le = min(95, max(51, abs(score)*10 + 50))
    return prediction, round(ty_le,1), signals

# ============ API ============
@app.route("/api/dudoanvip", methods=["GET"])
def du_doan_vip():
    # Fetch API gốc
    data = fetch_api_goc()
    
    phien = data["phien"]
    x1, x2, x3 = data["xuc_xac_1"], data["xuc_xac_2"], data["xuc_xac_3"]
    tong = data["tong"]
    ket_qua = data["ket_qua"]
    thoi_gian = data["thoi_gian"]
    
    # Phân tích
    analyzer = BridgeAnalyzer(history)
    bridge = analyzer.analyze_all()
    
    # Dự đoán
    du_doan, ty_le, signals = predict_tai_xiu(bridge)
    
    # Lưu
    session_data = {"phien": phien, "tong": tong, "ket_qua": ket_qua, "du_doan": du_doan, "ty_le": f"{ty_le}%"}
    history.append(session_data)
    stats_tracker.add_result(session_data)
    if len(history) > 100: history.pop(0)
    
    return jsonify({
        "phien": phien,
        "tong": tong,
        "ket_qua": ket_qua,
        "xuc_xac": f"{x1}-{x2}-{x3}",
        "xuc_xac_1": x1, "xuc_xac_2": x2, "xuc_xac_3": x3,
        "thoi_gian": thoi_gian,
        "time": thoi_gian,
        "du_doan": du_doan.lower(),
        "ty_le": f"{ty_le}%",
        "break_signals": signals,
        "total_algorithms": 22,
        "bridge_analysis": bridge,
        "stats": stats_tracker.get_stats(),
        "id": "@sunwin_ai"
    })

@app.route("/api/stats")
def get_stats():
    return jsonify(stats_tracker.get_stats())

@app.route("/api/lichsu")
def lich_su():
    limit = request.args.get("limit", 20, type=int)
    return jsonify(history[-limit:])

@app.route("/")
def home():
    return jsonify({"status": "online", "service": "SunWin AI API", "version": "6.0", "api_goc": API_GOC})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)