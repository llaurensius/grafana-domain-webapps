import React, { useState, useEffect } from 'react';
import client from '../api/client';
import Badge from '../components/UI/Badge';

const Incidents = () => {
  const [incidents, setIncidents] = useState([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchIncidents(currentPage, controller.signal);
    return () => controller.abort();
  }, [currentPage]);

  const fetchIncidents = async (page, signal) => {
    setIsLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * itemsPerPage;
      const res = await client.get(`/incidents/?skip=${skip}&limit=${itemsPerPage}`, { signal });
      setIncidents(res.data.data);
      setTotal(res.data.total);
    } catch (err) {
      if (err.name === 'CanceledError' || err.message === 'canceled') {
        // Request was aborted by rapid pagination, ignore
        return;
      }
      console.error(err);
      setError('Failed to fetch incidents.');
    } finally {
      setIsLoading(false);
    }
  };

  const totalPages = Math.ceil(total / itemsPerPage);

  return (
    <div>
      <div className="page-header">
        <h1>Incident History</h1>
      </div>

      <div className="card">
        <table className="table-container">
          <thead>
            <tr>
              <th>Domain</th>
              <th>Start Time</th>
              <th>End Time</th>
              <th>Duration (s)</th>
              <th>Status</th>
              <th>True Downtime</th>
              <th>Error Classification</th>
            </tr>
          </thead>
          <tbody style={{ opacity: isLoading ? 0.6 : 1, transition: 'opacity 0.2s' }}>
            {error ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '2rem', color: 'var(--danger-color)' }}>{error}</td>
              </tr>
            ) : incidents.length === 0 && !isLoading ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>No incidents found.</td>
              </tr>
            ) : (
              incidents.map(inc => (
                <tr key={inc.id}>
                  <td>
                    <strong>{inc.domain_name || inc.domain_id}</strong>
                    <br/>
                    <small style={{ color: 'var(--text-secondary)' }}>{inc.domain_url}</small>
                  </td>
                  <td>{new Date(inc.start_time).toLocaleString()}</td>
                  <td>{inc.end_time ? new Date(inc.end_time).toLocaleString() : '-'}</td>
                  <td>{inc.duration_seconds || '-'}</td>
                  <td>
                    <Badge type={inc.status === 'ACTIVE' ? 'danger' : 'success'}>{inc.status}</Badge>
                  </td>
                  <td>
                    {inc.qualifies_as_downtime ? <Badge type="danger">Yes (&gt; 5m)</Badge> : <Badge type="warning">Transient</Badge>}
                  </td>
                  <td style={{ color: 'var(--danger-color)', fontWeight: 500 }}>{inc.error_type || '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        
        {total > 0 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem', padding: '1rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, total)} of {total} entries (Page {currentPage} of {totalPages})</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))} 
                disabled={currentPage === 1 || isLoading}
                className="btn btn-secondary"
                style={{ opacity: (currentPage === 1 || isLoading) ? 0.5 : 1 }}
              >
                Previous
              </button>
              <button 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} 
                disabled={currentPage === totalPages || isLoading}
                className="btn btn-secondary"
                style={{ opacity: (currentPage === totalPages || isLoading) ? 0.5 : 1 }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Incidents;
