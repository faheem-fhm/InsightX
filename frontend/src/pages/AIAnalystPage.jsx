import React, { useState, useEffect, useRef } from "react";
import { useDataset } from "../context/DatasetContext";
import { datasetApi } from "../services/api";
import ChartRenderer from "../components/charts/ChartRenderer";
import CustomChartBuilder from "../components/charts/CustomChartBuilder";
import NoDatasetState from "../components/common/NoDatasetState";
import {
  Bot,
  Send,
  Code,
  Sparkles,
  BookOpen,
  BarChart2,
  ChevronDown,
  ChevronUp,
  Loader,
  RefreshCw,
  Trash2,
  PlusCircle,
  X,
} from "lucide-react";

/* ── Typing indicator dots ────────────────────────────────────────────────── */
function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3 py-2">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

/* ── Single AI response card ─────────────────────────────────────────────── */
function AssistantCard({ msg, idx, showSql, toggleSql }) {
  // If this is the initial greeting or intro message, show clean short intro of what the analyst does
  if (msg.is_intro || msg.finding === "InsightX Data Analyst ready." || msg.finding === "Conversation cleared.") {
    return (
      <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/40 border border-slate-800 mr-4 md:mr-12 space-y-3 shadow-lg">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100">InsightX AI Data Analyst Ready</h3>
            <span className="text-[11px] text-slate-400">
              {msg.evidence || "Connected to verified dataset records"}
            </span>
          </div>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed font-medium">
          I am your AI Data Analyst. Ask me any analytical question about your dataset, and I will query the data, analyze patterns, and provide clear insights and recommendations based on your dataset records.
        </p>
      </div>
    );
  }

  return (
    <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 mr-4 md:mr-12">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
          Analytical Finding
        </span>
        <div className="flex items-center gap-2">
          {msg.rag_chunks_used > 0 && (
            <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">
              <BookOpen className="w-2.5 h-2.5" />
              {msg.rag_chunks_used} RAG source{msg.rag_chunks_used !== 1 ? "s" : ""}
            </span>
          )}
          {msg.confidence && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400">
              Confidence: {msg.confidence}
            </span>
          )}
        </div>
      </div>

      <p className="text-base font-bold text-slate-100 mb-3">{msg.finding}</p>

      {/* Evidence (Actual Data) & Explanation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs mb-3">
        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
          <span className="font-bold text-slate-400 block mb-1">Evidence (Actual Data)</span>
          <p className="text-slate-300 mb-2">{msg.evidence}</p>
          {Array.isArray(msg.raw_data) && msg.raw_data.length > 0 && (
            <div className="overflow-x-auto max-h-48 rounded border border-slate-800/80 mt-2">
              <table className="w-full text-[11px] text-left">
                <thead className="bg-slate-900 text-slate-400 font-semibold sticky top-0 border-b border-slate-800">
                  <tr>
                    {Object.keys(msg.raw_data[0]).map((col) => (
                      <th key={col} className="px-2 py-1 whitespace-nowrap capitalize">
                        {col.replace(/_/g, " ")}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {msg.raw_data.slice(0, 10).map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-900/40">
                      {Object.entries(row).map(([k, val], cIdx) => (
                        <td key={cIdx} className="px-2 py-1 text-slate-300 font-mono whitespace-nowrap">
                          {typeof val === "number"
                            ? k.includes("$")
                              ? (val < 0 ? `-$${Math.abs(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`)
                              : val.toLocaleString(undefined, { maximumFractionDigits: 2 })
                            : String(val ?? "—")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {msg.raw_data.length > 10 && (
                <div className="text-[10px] text-slate-500 text-center py-1 bg-slate-900/60 border-t border-slate-800">
                  Showing top 10 of {msg.raw_data.length} rows
                </div>
              )}
            </div>
          )}
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
          <div>
            <span className="font-bold text-slate-400 block mb-1">Explanation</span>
            <p className="text-slate-300 whitespace-pre-line leading-relaxed font-medium">{msg.explanation}</p>
          </div>
          <div className="mt-3 pt-2 border-t border-slate-900 text-[10px] text-slate-500 italic">
            *Calculated directly from verified dataset records.
          </div>
        </div>
      </div>

      {/* Recommendation */}
      {msg.recommendation && (
        <div className="p-3.5 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-xs mb-3">
          <span className="font-bold text-emerald-400 block mb-1">Recommendation</span>
          <p className="text-slate-300 leading-relaxed font-medium">{msg.recommendation}</p>
        </div>
      )}

      {/* Generated Chart */}
      {msg.chart_spec && msg.chart_spec.data && msg.chart_spec.data.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 mb-3">
          <h4 className="text-xs font-bold text-slate-300 mb-2">{msg.chart_spec.title}</h4>
          <ChartRenderer spec={msg.chart_spec} />
        </div>
      )}

      {/* SQL Inspector */}
      {msg.sql_query && (
        <div>
          <button
            onClick={() => toggleSql(idx)}
            className="text-[11px] font-semibold text-slate-500 hover:text-indigo-400 flex items-center gap-1.5 transition"
          >
            <Code className="w-3.5 h-3.5" />
            {showSql[idx] ? "Hide" : "View"} Verified SQL
            {showSql[idx] ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
          {showSql[idx] && (
            <pre className="mt-2 p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] font-mono text-emerald-400 overflow-x-auto">
              {msg.sql_query}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Main Page ────────────────────────────────────────────────────────────── */
export default function AIAnalystPage() {
  const { currentDataset } = useDataset();
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [asking, setAsking] = useState(false);
  const [showSql, setShowSql] = useState({});
  const [suggestedPrompts, setSuggestedPrompts] = useState([]);
  const [loadingPrompts, setLoadingPrompts] = useState(false);
  const [buildingProfile, setBuildingProfile] = useState(false);
  const [showChartBuilder, setShowChartBuilder] = useState(false);
  const [customCharts, setCustomCharts] = useState([]);
  const bottomRef = useRef(null);

  // Reset + initialize when dataset changes
  useEffect(() => {
    if (!currentDataset?.id) return;

    // Reset state
    setMessages([
      {
        role: "assistant",
        is_intro: true,
        finding: "InsightX Data Analyst ready.",
        evidence: `Connected to ${currentDataset.name} (${currentDataset.row_count?.toLocaleString() ?? 0} records).`,
      },
    ]);
    setShowSql({});
    setCustomCharts([]);
    setShowChartBuilder(false);

    // Load suggested prompts from RAG profile
    loadSuggestedPrompts();
  }, [currentDataset?.id]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, asking]);

  if (!currentDataset?.id) {
    return <NoDatasetState title="No Active Dataset Selected" />;
  }

  const loadSuggestedPrompts = async () => {
    setLoadingPrompts(true);
    try {
      const res = await datasetApi.getSuggestedPrompts(currentDataset.id);
      setSuggestedPrompts(res.data.prompts || []);
    } catch {
      // Fallback tailored prompts using target_column if no RAG profile yet
      const targetName = currentDataset.target_column ? currentDataset.target_column.replace(/_/g, " ") : "the target metric";
      setSuggestedPrompts([
        `What drives ${targetName} the most?`,
        `Why does ${targetName} increase or decrease?`,
        `What is the breakdown of ${targetName} across categories?`,
        "Show a statistical summary of the dataset.",
        "Find unusual anomalies or outliers.",
      ]);
    } finally {
      setLoadingPrompts(false);
    }
  };

  const handleBuildProfile = async () => {
    setBuildingProfile(true);
    try {
      const res = await datasetApi.buildRagProfile(currentDataset.id);
      setSuggestedPrompts(res.data.suggested_prompts || []);
      // Show confirmation in chat
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          finding: `RAG profile built: ${res.data.chunks_built} knowledge chunks indexed.`,
          evidence: "Dataset statistics, column distributions, and correlations have been profiled.",
          explanation:
            "The AI Analyst now has a richer understanding of your dataset. Answers will be more grounded and context-aware.",
          recommendation: "Try asking about trends, comparisons, or root causes now.",
          confidence: "High",
          rag_chunks_used: 0,
        },
      ]);
    } catch (err) {
      console.error("RAG profile build failed:", err);
    } finally {
      setBuildingProfile(false);
    }
  };

  const toggleSql = (idx) =>
    setShowSql((prev) => ({ ...prev, [idx]: !prev[idx] }));

  const handleAsk = async (textToAsk) => {
    const prompt = textToAsk || query;
    if (!prompt.trim() || !currentDataset?.id) return;

    setMessages((prev) => [...prev, { role: "user", text: prompt }]);
    setQuery("");
    setAsking(true);

    try {
      const res = await datasetApi.askAI(currentDataset.id, { question: prompt });
      setMessages((prev) => [...prev, { role: "assistant", ...res.data }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          finding: "Unable to process query.",
          evidence: "Query execution failed.",
          explanation:
            err.response?.data?.detail || "An error occurred while evaluating the query.",
          recommendation: "Refine the question or ensure the dataset contains relevant columns.",
          confidence: "Low",
          rag_chunks_used: 0,
        },
      ]);
    } finally {
      setAsking(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: "assistant",
        is_intro: true,
        finding: "Conversation cleared.",
        evidence: `Still connected to ${currentDataset.name}.`,
      },
    ]);
    setShowSql({});
  };

  const handleAddCustomChartToDashboard = (chartSpec) => {
    setCustomCharts((prev) => [...prev, { ...chartSpec, id: `custom_${Date.now()}` }]);
    setShowChartBuilder(false);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight flex items-center gap-2">
            <Bot className="w-6 h-6 text-indigo-400" /> Interactive AI Data Analyst
          </h1>
          <p className="text-sm text-slate-400">
            RAG-powered analytics · AST-validated SQL · Domain-aware LLM insights
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {/* Rebuild RAG Profile */}
          <button
            onClick={handleBuildProfile}
            disabled={buildingProfile}
            title="Rebuild the RAG knowledge profile for richer AI context"
            className="px-3 py-1.5 rounded-lg bg-violet-600/15 text-violet-400 border border-violet-500/30 text-xs font-bold hover:bg-violet-600/25 transition flex items-center gap-1.5 disabled:opacity-60"
          >
            {buildingProfile ? (
              <Loader className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <RefreshCw className="w-3.5 h-3.5" />
            )}
            {buildingProfile ? "Indexing..." : "Rebuild RAG Index"}
          </button>

          {/* Custom Chart Builder Toggle */}
          <button
            onClick={() => setShowChartBuilder((v) => !v)}
            className={`px-3 py-1.5 rounded-lg border text-xs font-bold transition flex items-center gap-1.5 ${
              showChartBuilder
                ? "bg-emerald-600/20 text-emerald-400 border-emerald-500/30"
                : "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            Build Custom Chart
          </button>

          {/* Clear Chat */}
          <button
            onClick={handleClearChat}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-slate-300 transition"
            title="Clear conversation"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* ── Custom Chart Builder Panel ───────────────────────────────────── */}
      {showChartBuilder && (
        <div className="rounded-2xl border border-emerald-500/20 bg-slate-900/90 p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-emerald-300 flex items-center gap-2">
                <BarChart2 className="w-4 h-4" /> Custom Chart Builder
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Select columns from your dataset to generate any chart instantly.
              </p>
            </div>
            <button
              onClick={() => setShowChartBuilder(false)}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <CustomChartBuilder
            datasetId={currentDataset.id}
            onAddToDashboard={handleAddCustomChartToDashboard}
          />
        </div>
      )}

      {/* ── Custom Charts (added to this page) ──────────────────────────── */}
      {customCharts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <PlusCircle className="w-3.5 h-3.5 text-emerald-400" /> Your Custom Charts
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {customCharts.map((spec) => (
              <div key={spec.id} className="p-5 rounded-2xl bg-slate-900 border border-emerald-500/15 relative group">
                <button
                  onClick={() => setCustomCharts((prev) => prev.filter((c) => c.id !== spec.id))}
                  className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 p-1 rounded bg-slate-800 hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 border border-slate-700 hover:border-rose-500/30 transition"
                >
                  <X className="w-3 h-3" />
                </button>
                <h4 className="text-xs font-bold text-slate-200 mb-1">{spec.title}</h4>
                <p className="text-[10px] text-slate-500 mb-3">{spec.description}</p>
                <ChartRenderer spec={spec} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Suggested Prompt Chips ───────────────────────────────────────── */}
      <div className="flex items-start gap-2 overflow-x-auto pb-1">
        <Sparkles className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0 mt-1" />
        <div className="flex gap-2 flex-wrap">
          {loadingPrompts ? (
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Loader className="w-3 h-3 animate-spin" /> Loading smart prompts...
            </span>
          ) : (
            suggestedPrompts.map((p, i) => (
              <button
                key={i}
                onClick={() => handleAsk(p)}
                className="px-3 py-1.5 rounded-full text-xs font-medium bg-slate-900 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800 text-slate-300 whitespace-nowrap transition"
              >
                {p}
              </button>
            ))
          )}
        </div>
      </div>

      {/* ── Chat Messages ────────────────────────────────────────────────── */}
      <div className="space-y-4 pb-4">
        {messages.map((msg, i) =>
          msg.role === "user" ? (
            <div
              key={i}
              className="p-4 rounded-2xl bg-indigo-600/10 border border-indigo-500/25 ml-4 md:ml-12"
            >
              <p className="text-sm font-semibold text-indigo-300">{msg.text}</p>
            </div>
          ) : (
            <AssistantCard
              key={i}
              msg={msg}
              idx={i}
              showSql={showSql}
              toggleSql={toggleSql}
            />
          )
        )}

        {/* Typing indicator */}
        {asking && (
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 mr-4 md:mr-12">
            <div className="flex items-center gap-2 text-xs text-indigo-400 mb-2">
              <Bot className="w-3.5 h-3.5" /> Analysing dataset with RAG context...
            </div>
            <TypingIndicator />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Sticky Input ─────────────────────────────────────────────────── */}
      <div className="sticky bottom-4 bg-slate-900 border border-slate-700 rounded-xl p-2 flex items-center gap-2 shadow-2xl">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          placeholder="Ask anything about the dataset, trends, or root causes..."
          className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none"
        />
        <button
          onClick={() => handleAsk()}
          disabled={asking || !query.trim()}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition flex items-center gap-1.5 disabled:opacity-50"
        >
          {asking ? <Loader className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
          {asking ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
}
