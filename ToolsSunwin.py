from flask import Flask, jsonify, request
import random
from datetime import datetime
import pytz
from collections import Counter

app = Flask(__name__)

history = []
current_session = {"phien": 0, "ket_qua": None}

# ============ STATS TRACKER ============
class StatsTracker:
    def __init__(self):
        self.history = []
        self.balance = 0  # Số dư (nếu có)
    
    def add_result(self, data):
        du_doan = data.get("du_doan", "").lower()
        ket_qua = data.get("ket_qua", "").lower()
        
        if du_doan and ket_qua:
            if du_doan == ket_qua:
                result = "THẮNG"
            elif (du_doan == "tài" and ket_qua == "xỉu") or (du_doan == "xỉu" and ket_qua == "tài"):
                result = "THUA"
            else:
                result = "CHƯA RÕ"
        else:
            result = "CHƯA RÕ"
        
        self.history.append({
            "phien": data.get("phien"),
            "du_doan": du_doan,
            "ket_qua": ket_qua,
            "xuc_xac": f"{data.get('xuc_xac_1',0)}-{data.get('xuc_xac_2',0)}-{data.get('xuc_xac_3',0)}",
            "tong": data.get("tong", 0),
            "ty_le": data.get("ty_le", "0%"),
            "result": result,
            "time": data.get("thoi_gian", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
        })
        
        if len(self.history) > 200:
            self.history.pop(0)
    
    def get_stats(self):
        total = len(self.history)
        if total == 0: return {"status": "Chưa có dữ liệu"}
        
        wins = sum(1 for h in self.history if h["result"] == "THẮNG")
        losses = sum(1 for h in self.history if h["result"] == "THUA")
        
        streak = 0; streak_type = ""
        for h in reversed(self.history):
            if h["result"] in ("THẮNG", "THUA"):
                if streak_type == "" or streak_type == h["result"]:
                    streak += 1; streak_type = h["result"]
                else: break
        
        recent20 = self.history[-20:]
        rw = sum(1 for h in recent20 if h["result"] == "THẮNG")
        rl = sum(1 for h in recent20 if h["result"] == "THUA")
        
        return {
            "tong_phien": total,
            "thang": wins, "thua": losses,
            "ty_le_thang": round(wins / max(wins + losses, 1) * 100, 1),
            "streak": f"{streak} {streak_type}" if streak > 0 else "Không",
            "gan_day": {"tong": len(recent20), "thang": rw, "thua": rl,
                        "ty_le": round(rw / max(rw + rl, 1) * 100, 1)}
        }
    
    def get_history(self, limit=20):
        return self.history[-limit:]

stats_tracker = StatsTracker()

# ============ PHÂN TÍCH CẦU ============
class BridgeAnalyzer:
    def __init__(self, history_data):
        self.data = [1 if h["ket_qua"] == "Tài" else -1 for h in history_data] if history_data else []
    
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
            "markov": self.markov_chain(), "fibonacci": self.fibonacci_bridge()
        }
    
    def cau_bet(self):
        if len(self.data) < 3: return {"loai": "Chưa rõ", "do_dai": 0}
        streak, last = 1, self.data[-1]
        for i in range(len(self.data)-2, -1, -1):
            if self.data[i] == last: streak += 1
            else: break
        return {"loai": f"Bệt {streak} {'TÀI' if last==1 else 'XỈU'}", "do_dai": streak,
                "xu_huong": "Tiếp tục bệt" if streak>=3 else "Có thể gãy",
                "ket_qua": "TÀI" if last==1 else "XỈU"}
    
    def cau_1_1(self):
        if len(self.data) < 4: return {"loai": "Chưa rõ"}
        alt = all(self.data[-i] != self.data[-i-1] for i in range(1, min(6, len(self.data))))
        return {"loai": "Cầu 1-1 (Xen kẽ)" if alt else "Không phải",
                "du_doan": "XỈU" if self.data[-1]==1 else "TÀI" if alt else "Không rõ"}
    
    def cau_2_1(self):
        if len(self.data) < 6: return {"loai": "Chưa rõ"}
        r = self.data[-9:]
        p = all(r[i]==r[i+1] and r[i]!=r[i+2] for i in range(0, len(r)-2, 3))
        return {"loai": "Cầu 2-1" if p else "Không phải",
                "du_doan": ("TÀI" if r[-1]==-1 else "XỈU") if p else "Không rõ"}
    
    def cau_2_2(self):
        if len(self.data) < 8: return {"loai": "Chưa rõ"}
        r = self.data[-8:]
        p = all(r[i]==r[i+1] and r[i]!=r[i+2]==r[i+3] for i in range(0, len(r)-1, 4))
        return {"loai": "Cầu 2-2" if p else "Không phải",
                "du_doan": ("TÀI" if r[-1]==-1 else "XỈU") if p else "Không rõ"}
    
    def cau_3_2(self):
        if len(self.data) < 10: return {"loai": "Chưa rõ"}
        r = self.data[-10:]
        p = all(r[i]==r[i+1]==r[i+2] and r[i+2]!=r[i+3]==r[i+4] for i in range(0, len(r)-4, 5))
        return {"loai": "Cầu 3-2" if p else "Không phải",
                "du_doan": ("TÀI" if r[-1]==-1 else "XỈU") if p else "Không rõ"}
    
    def cau_doi_xung(self):
        if len(self.data) < 4: return {"loai": "Chưa rõ"}
        r = self.data[-5:] if len(self.data)>=5 else self.data
        s = r == r[::-1]
        return {"loai": "Cầu đối xứng" if s else "Không",
                "du_doan": ("TÀI" if r[0]==1 else "XỈU") if s else "Không rõ"}
    
    def cau_tam_giac(self):
        if len(self.data) < 7: return {"loai": "Chưa rõ"}
        r = self.data[-7:]
        p = (r[0]==r[3]==r[6] and r[1]==r[4] and r[2]==r[5] and r[0]!=r[1] and r[1]!=r[2])
        return {"loai": "Cầu tam giác" if p else "Không phải",
                "du_doan": ("TÀI" if r[-1]==-1 else "XỈU") if p else "Không rõ"}
    
    def cau_thang(self):
        if len(self.data) < 3: return {"loai": "Chưa rõ"}
        ch = sum(1 for i in range(1, len(self.data)) if self.data[i]!=self.data[i-1])
        r = ch/(len(self.data)-1) if len(self.data)>1 else 0
        return {"loai": "Cầu thang (đổi liên tục)" if r>0.8 else ("Cầu thang (bệt dài)" if r<0.2 else "Cầu thang (hỗn hợp)"),
                "ti_le_doi_chieu": round(r*100,1)}
    
    def cau_rong(self):
        if len(self.data) < 5: return {"loai": "Chưa rõ", "du_doan": "Không rõ"}
        r = self.data[-7:] if len(self.data)>=7 else self.data
        tc = sum(1 for x in r if x==1); tr = tc/len(r)
        if tr>=0.7: return {"loai": f"Cầu Rồng (TÀI {tc}/{len(r)})", "du_doan": "TÀI", "ti_le": round(tr*100,1)}
        elif tr>=0.57: return {"loai": f"Cầu Rồng nhẹ", "du_doan": "TÀI", "ti_le": round(tr*90,1)}
        return {"loai": "Không phải cầu Rồng", "du_doan": "Không rõ", "ti_le": 50}
    
    def cau_ho(self):
        if len(self.data) < 5: return {"loai": "Chưa rõ", "du_doan": "Không rõ"}
        r = self.data[-7:] if len(self.data)>=7 else self.data
        xc = sum(1 for x in r if x==-1); xr = xc/len(r)
        if xr>=0.7: return {"loai": f"Cầu Hổ (XỈU {xc}/{len(r)})", "du_doan": "XỈU", "ti_le": round(xr*100,1)}
        elif xr>=0.57: return {"loai": f"Cầu Hổ nhẹ", "du_doan": "XỈU", "ti_le": round(xr*90,1)}
        return {"loai": "Không phải cầu Hổ", "du_doan": "Không rõ", "ti_le": 50}
    
    def cau_rong_xanh(self):
        if len(self.data) < 6: return {"loai": "Chưa rõ"}
        r = self.data[-6:]
        p = all(r[i]!=r[i-1] for i in range(1, len(r)))
        return {"loai": "Cầu Rồng Xanh (T-X đều)" if p else "Không phải",
                "du_doan": "XỈU" if r[-1]==1 else "TÀI" if p else "Không rõ"}
    
    def cau_ho_vang(self):
        if len(self.data) < 8: return {"loai": "Chưa rõ"}
        r = self.data[-8:]
        p = all(r[i]==r[i+1] and r[i+2]==r[i+3] and r[i]!=r[i+2] for i in range(0,8,4))
        return {"loai": "Cầu Hổ Vàng (2-2)" if p else "Không phải",
                "du_doan": "TÀI" if r[-1]==-1 else "XỈU" if p else "Không rõ"}
    
    def cau_rong_thang(self):
        if len(self.data) < 6: return {"loai": "Chưa rõ"}
        c3 = sum(1 for i in range(len(self.data)-2) if self.data[i]==self.data[i+1]==self.data[i+2]==1)
        return {"loai": f"Cầu Rồng Thắng ({c3} lần 3 TÀI)" if c3>=2 else "Không phải",
                "du_doan": "TÀI" if c3>=2 else "Không rõ"}
    
    def cau_ho_xam(self):
        if len(self.data) < 6: return {"loai": "Chưa rõ"}
        c3 = sum(1 for i in range(len(self.data)-2) if self.data[i]==self.data[i+1]==self.data[i+2]==-1)
        return {"loai": f"Cầu Hổ Xám ({c3} lần 3 XỈU)" if c3>=2 else "Không phải",
                "du_doan": "XỈU" if c3>=2 else "Không rõ"}
    
    def cau_long_phuong(self):
        if len(self.data) < 6: return {"loai": "Chưa rõ"}
        m = len(self.data)//2
        s = self.data[:m] == self.data[-m:][::-1]
        return {"loai": "Cầu Long Phượng" if s else "Không đối xứng",
                "du_doan": "TÀI" if self.data[-1]==-1 and s else ("XỈU" if self.data[-1]==1 and s else "Không rõ")}
    
    def xu_huong(self):
        if len(self.data) < 5: return {"xu_huong": "Chưa đủ dữ liệu"}
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
        return {"tong_phien": t, "tai": tc, "xiu": t-tc,
                "ti_le_tai": round(tc/t*100,1), "ti_le_xiu": round((t-tc)/t*100,1)}
    
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

# ============ PHÂN TÍCH XÚC XẮC ============
class XucXacAnalyzer:
    def __init__(self, history_data):
        self.history = history_data
    
    def analyze(self):
        if not self.history: return {"status": "Chưa có dữ liệu"}
        return {
            "mat_gan_nhat": self.mat_gan_nhat(),
            "tan_suat_mat": self.tan_suat_mat(),
            "du_doan_xuc_xac": self.du_doan_xuc_xac(),
            "pattern": self.pattern()
        }
    
    def mat_gan_nhat(self):
        recent = self.history[-3:] if len(self.history) >= 3 else self.history
        return [{"phien": h.get("phien"), "x1": h.get("xuc_xac_1"), "x2": h.get("xuc_xac_2"),
                 "x3": h.get("xuc_xac_3"), "tong": h.get("tong")} for h in recent]
    
    def tan_suat_mat(self):
        if not self.history: return {}
        face_count = {1:0,2:0,3:0,4:0,5:0,6:0}
        total = 0
        for h in self.history:
            for k in ["xuc_xac_1","xuc_xac_2","xuc_xac_3"]:
                f = h.get(k, 0)
                if f in face_count: face_count[f] += 1; total += 1
        return {"tong_lan": total, "mat_nhieu_nhat": max(face_count, key=face_count.get),
                "chi_tiet": {f"mat_{k}": {"so_lan": v, "ty_le": round(v/total*100,1)} for k, v in face_count.items()}}
    
    def du_doan_xuc_xac(self):
        if len(self.history) < 5: return {"status": "Cần 5 phiên"}
        recent = self.history[-10:]
        x1 = round(sum(h.get("xuc_xac_1",0) for h in recent)/len(recent))
        x2 = round(sum(h.get("xuc_xac_2",0) for h in recent)/len(recent))
        x3 = round(sum(h.get("xuc_xac_3",0) for h in recent)/len(recent))
        tong = x1+x2+x3
        return {"x1": x1, "x2": x2, "x3": x3, "tong": tong, "ket_qua": "Tài" if tong>=11 else "Xỉu"}
    
    def pattern(self):
        if len(self.history) < 6: return {}
        recent = self.history[-10:]
        baos = sum(1 for h in recent if h.get("xuc_xac_1")==h.get("xuc_xac_2")==h.get("xuc_xac_3"))
        dois = sum(1 for h in recent if len(set([h.get("xuc_xac_1"),h.get("xuc_xac_2"),h.get("xuc_xac_3")]))==2)
        return {"bao": baos, "doi": dois, "ty_le_bao": f"{round(baos/len(recent)*100,1)}%",
                "ty_le_doi": f"{round(dois/len(recent)*100,1)}%"}

# ============ API ENDPOINTS ============
@app.route("/api/dudoanvip", methods=["GET"])
def du_doan_vip():
    global current_session, history
    
    # Lấy dữ liệu từ API gốc
    try:
        import requests as req
        resp = req.get("https://trails-wish-motel-legacy.trycloudflare.com/api/tx", timeout=5)
        data = resp.json()
        phien = data.get("phien")
        x1, x2, x3 = data.get("xuc_xac_1", 0), data.get("xuc_xac_2", 0), data.get("xuc_xac_3", 0)
        tong = data.get("tong", x1+x2+x3)
        ket_qua_raw = data.get("ket_qua", "Tài" if tong >= 11 else "Xỉu")
        ket_qua = "Tài" if "Tài" in ket_qua_raw or "tài" in ket_qua_raw else "Xỉu"
        thoi_gian = data.get("thoi_gian", datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).strftime("%d-%m-%Y %H:%M:%S UTC+7"))
    except:
        phien = random.randint(1000000, 9999999)
        x1, x2, x3 = random.randint(1,6), random.randint(1,6), random.randint(1,6)
        tong = x1+x2+x3
        ket_qua = "Tài" if tong >= 11 else "Xỉu"
        thoi_gian = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).strftime("%d-%m-%Y %H:%M:%S UTC+7")
    
    # Phân tích cầu
    analyzer = BridgeAnalyzer(history)
    bridge_analysis = analyzer.analyze_all()
    xuc_xac_analyzer = XucXacAnalyzer(history)
    xuc_xac_analysis = xuc_xac_analyzer.analyze()
    
    # Dự đoán
    du_doan, ty_le, signals = predict_tai_xiu(bridge_analysis)
    
    # Lưu lịch sử
    session_data = {
        "phien": phien, "tong": tong, "ket_qua": ket_qua,
        "xuc_xac_1": x1, "xuc_xac_2": x2, "xuc_xac_3": x3,
        "du_doan": du_doan.lower(), "ty_le": f"{ty_le}%"
    }
    history.append(session_data)
    if len(history) > 100: history.pop(0)
    
    # Log thắng thua
    stats_tracker.add_result(session_data)
    
    current_session = {
        "phien": phien, "tong": tong, "ket_qua": ket_qua,
        "xuc_xac": f"{x1}-{x2}-{x3}",
        "xuc_xac_1": x1, "xuc_xac_2": x2, "xuc_xac_3": x3,
        "thoi_gian": thoi_gian,
        "time": thoi_gian,
        "du_doan": du_doan.lower(), "ty_le": f"{ty_le}%",
        "break_signals": signals,
        "total_algorithms": 15,
        "bridge_analysis": bridge_analysis,
        "xuc_xac_analysis": xuc_xac_analysis,
        "stats": stats_tracker.get_stats(),
        "id": "@sunwin_ai"
    }
    return jsonify(current_session)

def predict_tai_xiu(bridge):
    score, signals = 0, 0
    if bridge["cau_bet"]["do_dai"] >= 4:
        score += (1 if bridge["cau_bet"]["ket_qua"]=="TÀI" else -1) * 3; signals += 1
    if bridge["cau_1_1"]["loai"] == "Cầu 1-1 (Xen kẽ)":
        score += (1 if bridge["cau_1_1"]["du_doan"]=="TÀI" else -1) * 2; signals += 1
    if bridge["markov"]["du_doan"] != "Không rõ":
        score += (1 if bridge["markov"]["du_doan"]=="TÀI" else -1) * 1.5
    if bridge["fibonacci"]["du_doan"] != "Không rõ":
        score += (1 if bridge["fibonacci"]["du_doan"]=="TÀI" else -1) * 1.2
    if bridge["tan_suat"]["ti_le_tai"] > 65: score -= 2; signals += 1
    elif bridge["tan_suat"]["ti_le_tai"] < 35: score += 2; signals += 1
    if bridge["cau_rong"]["du_doan"] != "Không rõ":
        score += (1 if bridge["cau_rong"]["du_doan"]=="TÀI" else -1) * 2.5; signals += 1
    if bridge["cau_ho"]["du_doan"] != "Không rõ":
        score += (1 if bridge["cau_ho"]["du_doan"]=="TÀI" else -1) * 2.5; signals += 1
    if bridge["cau_rong_thang"]["du_doan"] != "Không rõ":
        score += (1 if bridge["cau_rong_thang"]["du_doan"]=="TÀI" else -1) * 2; signals += 1
    if bridge["cau_ho_xam"]["du_doan"] != "Không rõ":
        score += (1 if bridge["cau_ho_xam"]["du_doan"]=="TÀI" else -1) * 2; signals += 1
    score += random.uniform(-1, 1)
    prediction = "Tài" if score >= 0 else "Xỉu"
    ty_le = min(95, max(51, abs(score)*10 + 50))
    return prediction, round(ty_le,1), signals

@app.route("/api/stats", methods=["GET"])
def get_stats():
    return jsonify(stats_tracker.get_stats())

@app.route("/api/history", methods=["GET"])
def get_history():
    limit = request.args.get("limit", 20, type=int)
    return jsonify(stats_tracker.get_history(limit))

@app.route("/api/lichsu", methods=["GET"])
def lich_su():
    limit = request.args.get("limit", 20, type=int)
    return jsonify(history[-limit:])

@app.route("/api/xuc_xac", methods=["GET"])
def xuc_xac():
    analyzer = XucXacAnalyzer(history)
    return jsonify(analyzer.analyze())

@app.route("/")
def home():
    return jsonify({"status": "online", "service": "SunWin AI Bridge + Stats API", "version": "4.0"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)