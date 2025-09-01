import os
import time
import json
from typing import Dict, List, Tuple, Optional

import numpy as np


class LLMViewsGenerator:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        # lazy import to avoid hard dependency if key missing
        self._client = None

    def _ensure_client(self):
        if self._client is None and self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                self._client = None

    def generate(
        self,
        date_str: str,
        tickers: List[str],
        window_returns: Dict[str, List[float]],
        num_samples: int = 3,
        use_api: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, List[int]]:

        # If no key/client, fallback to a simple heuristic using recent mean returns
        self._ensure_client()
        if not use_api or self._client is None:
            mus = []
            vars_ = []
            for t in tickers:
                r = window_returns.get(t, [])
                if len(r) == 0:
                    mus.append(0.0)
                    vars_.append(0.0004)
                else:
                    mus.append(float(np.mean(r)))
                    vars_.append(float(np.var(r)) + 1e-4)
            mu = np.array(mus)
            Omega_diag = np.array(vars_)
            # build P as identity to express per-asset views
            P = np.eye(len(tickers))
            Q = mu
            Omega = np.diag(Omega_diag)
            return P, Q, Omega

        # With LLM: query per ticker and aggregate mean/variance of predicted avg daily return next two weeks
        # Clamp predictions to a reasonable range to avoid runaway allocations
        mus = []
        vars_ = []
        for t in tickers:
            series = window_returns.get(t, [])
            if len(series) == 0:
                mus.append(0.0)
                vars_.append(0.0004)
                continue
            prompt = (
                f"You are positioned on {date_str} market close. Use only the PAST two weeks.\n"
                f"Daily returns for {t}: {','.join([str(round(x,6)) for x in series])}.\n"
                "Predict the average DAILY return for the NEXT two weeks (10 trading days). "
                "Return strict JSON: {\"avg_daily_return\": number}."
            )
            samples = []
            for _ in range(num_samples):
                try:
                    resp = self._client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You output strict JSON only."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.8,
                    )
                    content = resp.choices[0].message.content
                    data = json.loads(content)
                    val = float(data.get("avg_daily_return", 0.0))
                    samples.append(val)
                    time.sleep(0.05)
                except Exception:
                    continue
            if len(samples) == 0:
                mus.append(float(np.mean(series)))
                vars_.append(float(np.var(series)) + 1e-4)
            else:
                m = float(np.mean(samples))
                # cap daily mean between -2% and +2%
                m = max(min(m, 0.02), -0.02)
                mus.append(m)
                vars_.append(float(np.var(samples)) + 1e-6)

        mu = np.array(mus)
        Omega_diag = np.array(vars_)
        P = np.eye(len(tickers))
        Q = mu
        Omega = np.diag(Omega_diag)
        return P, Q, Omega


