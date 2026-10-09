from pathlib import Path
import pandas as pd
from rapidfuzz import fuzz

DATA=Path(__file__).resolve().parent.parent/"data"/"mock"

class ToolBox:
    """Reusable tools. Real APIs can replace these adapters without changing the engine."""
    def read_table(self, path):
        p=Path(path)
        if p.suffix.lower()==".csv": return pd.read_csv(p)
        return pd.read_excel(p)

    def calculate(self, expression):
        # Safe calculator for simple numeric expressions.
        allowed=set("0123456789.+-*/()% ")
        if not set(expression) <= allowed: raise ValueError("Unsafe expression")
        return eval(expression, {"__builtins__":{}})

    def inventory_restock(self, path=None):
        df=self.read_table(path or DATA/"inventory.csv")
        df["reorder_qty"]=(df["minimum_stock"]-df["current_stock"]).clip(lower=0)
        out=df[df.current_stock < df.minimum_stock].copy()
        return out[["sku","product_name","current_stock","minimum_stock","reorder_qty"]].to_dict("records")

    def price_validation(self, products=None, vendors=None):
        p=self.read_table(products or DATA/"products.csv")
        v=self.read_table(vendors or DATA/"vendor_prices.csv")
        m=p.merge(v,on="sku",how="inner",suffixes=("_internal","_vendor"))
        m["difference_pct"]=(abs(m.price_internal-m.price_vendor)/m.price_internal*100).round(2)
        m["exception"]=m.difference_pct>10
        return m.to_dict("records")

    def process_vendor_file(self, path=None):
        df=self.read_table(path or DATA/"vendor_products.csv")
        df.columns=[str(c).strip().lower().replace(" ","_") for c in df.columns]
        df["valid"]=df["sku"].notna() & df["product_name"].notna()
        invalid=df[~df.valid].copy()
        clean=df[df.valid].drop(columns=["valid"])
        return {"cleaned":clean.to_dict("records"),"invalid_rows":invalid.drop(columns=["valid"]).to_dict("records"),
                "valid_count":len(clean),"invalid_count":len(invalid)}

    def order_status(self, order_id=None, email=None):
        df=self.read_table(DATA/"orders.csv")
        hit=df[(df.order_id.astype(str)==str(order_id)) if order_id else (df.customer_email==email)]
        if hit.empty: return None
        return hit.iloc[0].to_dict()

    def duplicate_detection(self):
        df=self.read_table(DATA/"catalog.csv")
        groups=[]; seen=set()
        for i,row in df.iterrows():
            if i in seen: continue
            group=[]
            for j,other in df.iterrows():
                if j<=i: continue
                sku_exact=str(row.sku)==str(other.sku) and str(row.sku)!="nan"
                name_sim=fuzz.token_set_ratio(str(row.product_name),str(other.product_name))
                attr_sim=fuzz.token_set_ratio(str(row.attributes),str(other.attributes))
                if sku_exact or (name_sim>=85 and attr_sim>=75):
                    group.append(j); seen.add(j)
            if group:
                ids=[i]+group
                seen.add(i)
                groups.append({"products":[df.loc[k].to_dict() for k in ids],
                               "confidence":"definite" if len({df.loc[k,'sku'] for k in ids})==1 else "possible"})
        return groups

    def keyword_classification(self):
        df=self.read_table(DATA/"keywords.csv")
        rows=[]
        for _,r in df.iterrows():
            kw=str(r.keyword).lower()
            if any(x in kw for x in ["how","what","guide","tips"]): intent="informational"
            elif any(x in kw for x in ["buy","price","discount","deal"]): intent="transactional"
            elif any(x in kw for x in ["best","compare","review"]): intent="commercial"
            else: intent="navigational"
            rows.append({**r.to_dict(),"intent":intent,
                         "priority":"high" if len(kw.split())<=3 else "medium",
                         "recommended_target_page":f"/{str(r.category).lower().replace(' ','-')}"})
        return rows

    def assign_task(self, task=None):
        employees=self.read_table(DATA/"employees.csv")
        req=set(str(task or "python api development").lower().split())
        def score(row):
            skills=set(str(row.skills).lower().replace(","," ").split())
            match=len(req & skills)
            capacity=max(0,100-int(row.workload_pct))
            return match*20+capacity*.4
        employees["score"]=employees.apply(score,axis=1)
        e=employees.sort_values("score",ascending=False).iloc[0]
        if e.score < 30: return {"escalate":True,"reason":"No suitable employee with enough skill/capacity."}
        return {"recommended_employee":e.employee,"score":round(float(e.score),1),"reason":"Best skill match with available capacity.",
                "priority":"urgent" if task and "urgent" in task.lower() else "normal"}

    def performance_report(self):
        df=self.read_table(DATA/"execution_logs.csv")
        success=(df.status=="success").mean()*100
        avg=df.execution_time_ms.mean()
        errors=df[df.status!="success"].error.value_counts().to_dict()
        slow=df.groupby("workflow_id").execution_time_ms.mean().sort_values(ascending=False).head(3).to_dict()
        return {"success_rate_pct":round(success,2),"failure_rate_pct":round(100-success,2),
                "average_execution_time_ms":round(float(avg),2),"frequent_errors":errors,
                "slow_workflows":slow,
                "recommendations":["Investigate workflows above 10% failure rate.",
                                   "Optimize workflows with high average execution time."]}
