import React, { createContext, useContext, useState, useEffect } from "react";
import { datasetApi } from "../services/api";

const DatasetContext = createContext();

export function DatasetProvider({ children }) {
  const [datasets, setDatasets] = useState([]);
  const [currentDataset, setCurrentDataset] = useState(null);
  const [loading, setLoading] = useState(false);
  const [backendError, setBackendError] = useState(false);
  const LS_ACTIVE_KEY = "insightx_active_dataset_id";

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      const res = await datasetApi.list();
      setDatasets(res.data);
      setBackendError(false);
      if (res.data.length > 0) {
        const savedId = localStorage.getItem(LS_ACTIVE_KEY);
        const matched = savedId ? res.data.find((d) => (d.id || d.dataset_id) === savedId) : null;
        const targetToSet = matched || res.data[0];
        setCurrentDataset(targetToSet);
        if (targetToSet?.id) {
          localStorage.setItem(LS_ACTIVE_KEY, targetToSet.id || targetToSet.dataset_id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch datasets:", err);
      if (err.code === "ERR_NETWORK" || err.message?.includes("Network Error") || !err.response) {
        setBackendError(true);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const selectDataset = (dataset) => {
    if (!dataset) return;
    const normalized = {
      ...dataset,
      id: dataset.id || dataset.dataset_id
    };
    setCurrentDataset(normalized);
    if (normalized.id) {
      localStorage.setItem(LS_ACTIVE_KEY, normalized.id);
    }
  };

  const loadSampleDataset = async (key) => {
    try {
      setLoading(true);
      const res = await datasetApi.loadSample(key);
      const datasetObj = {
        ...res.data,
        id: res.data.id || res.data.dataset_id
      };
      setBackendError(false);
      await fetchDatasets();
      setCurrentDataset(datasetObj);
      return datasetObj;
    } catch (err) {
      console.error("Failed to load sample dataset:", err);
      if (err.code === "ERR_NETWORK" || err.message?.includes("Network Error") || !err.response) {
        setBackendError(true);
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteDataset = async (datasetId) => {
    try {
      setLoading(true);
      await datasetApi.deleteDataset(datasetId);
      setDatasets((prev) => prev.filter((d) => (d.id || d.dataset_id) !== datasetId));
      if (currentDataset && (currentDataset.id === datasetId || currentDataset.dataset_id === datasetId)) {
        const remaining = datasets.filter((d) => (d.id || d.dataset_id) !== datasetId);
        setCurrentDataset(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (err) {
      console.error("Failed to delete dataset:", err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateDatasetQuality = (datasetId, newScore) => {
    if (!datasetId || newScore === undefined || newScore === null) return;
    setCurrentDataset((prev) => {
      if (prev && (prev.id === datasetId || prev.dataset_id === datasetId)) {
        return { ...prev, quality_score: newScore };
      }
      return prev;
    });
    setDatasets((prev) =>
      prev.map((d) =>
        (d.id === datasetId || d.dataset_id === datasetId)
          ? { ...d, quality_score: newScore }
          : d
      )
    );
  };

  return (
    <DatasetContext.Provider
      value={{
        datasets,
        currentDataset,
        selectDataset,
        fetchDatasets,
        loadSampleDataset,
        deleteDataset,
        updateDatasetQuality,
        loading,
        backendError
      }}
    >
      {children}
    </DatasetContext.Provider>
  );
}

export const useDataset = () => useContext(DatasetContext);

