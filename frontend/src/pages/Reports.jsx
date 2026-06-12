import React, { useState } from 'react';
import client from '../api/client';
import Badge from '../components/UI/Badge';

const Reports = () => {
  const [period, setPeriod] = useState('daily');
  const [date, setDate] = useState('');
  const [month, setMonth] = useState('');
  const [week, setWeek] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Pagination for preview
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const buildQueryParams = (page) => {
    const params = new URLSearchParams();
    params.append('period', period);
    
    if (period === 'daily') {
      if (!date) throw new Error('Please select a date.');
      params.append('date', date);
    } else if (period === 'monthly') {
      if (!month) throw new Error('Please select a month.');
      params.append('month', month);
    } else if (period === 'weekly') {
      if (!month || !week) throw new Error('Please select a month and week.');
      params.append('month', month);
      params.append('week', week);
    }
    
    if (search.trim()) {
      params.append('search', search.trim());
    }
    
    if (statusFilter !== 'ALL') {
      params.append('status', statusFilter);
    }
    
    if (page) {
      params.append('skip', (page - 1) * itemsPerPage);
      params.append('limit', itemsPerPage);
    }
    
    return params;
  };

  const handlePreview = async (page = 1) => {
    setIsLoading(true);
    setError(null);
    try {
      const params = buildQueryParams(page);
      const res = await client.get(`/reports/preview?${params.toString()}`);
      setData(res.data.data);
      setTotal(res.data.total);
      setCurrentPage(page);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || 'Failed to fetch report preview.');
      setData([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    try {
      const params = buildQueryParams();
      // Use window.location or anchor tag to trigger download since it returns a file stream
      // But using token requires client to inject auth.
      // Easiest is to fetch as blob.
      client.get(`/reports/export?${params.toString()}`, { responseType: 'blob' })
        .then((response) => {
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          // Extract filename from header if possible, or fallback
          const disposition = response.headers['content-disposition'];
          let filename = 'report.xlsx';
          if (disposition && disposition.indexOf('attachment') !== -1) {
            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            const matches = filenameRegex.exec(disposition);
            if (matches != null && matches[1]) { 
              filename = matches[1].replace(/['"]/g, '');
            }
          }
          link.setAttribute('download', filename);
          document.body.appendChild(link);
          link.click();
          link.parentNode.removeChild(link);
        })
        .catch(err => {
          setError('Failed to download excel file.');
        });
    } catch (err) {
      setError(err.message);
    }
  };

  const totalPages = Math.ceil(total / itemsPerPage);

  // Trigger search when user presses Enter
  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      handlePreview(1);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Reports Export</h1>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: '1rem' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Period Type</label>
            <select 
              className="form-control" 
              value={period} 
              onChange={e => {
                setPeriod(e.target.value);
                setData([]);
                setTotal(0);
                setCurrentPage(1);
              }}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          {period === 'daily' && (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Date</label>
              <input 
                type="date" 
                className="form-control" 
                value={date} 
                onChange={e => setDate(e.target.value)} 
              />
            </div>
          )}

          {(period === 'weekly' || period === 'monthly') && (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Month</label>
              <input 
                type="month" 
                className="form-control" 
                value={month} 
                onChange={e => setMonth(e.target.value)} 
              />
            </div>
          )}

          {period === 'weekly' && (
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Week</label>
              <select className="form-control" value={week} onChange={e => setWeek(parseInt(e.target.value))}>
                <option value={1}>Week 1</option>
                <option value={2}>Week 2</option>
                <option value={3}>Week 3</option>
                <option value={4}>Week 4</option>
                <option value={5}>Week 5</option>
              </select>
            </div>
          )}
        </div>
        
        {/* Filters Row */}
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ marginBottom: 0, flex: 1, minWidth: '200px' }}>
            <label>Search</label>
            <input 
              type="text" 
              className="form-control" 
              placeholder="Search domains..." 
              value={search} 
              onChange={e => setSearch(e.target.value)}
              onKeyDown={handleSearchKeyDown}
            />
          </div>
          
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Status</label>
            <select 
              className="form-control" 
              value={statusFilter} 
              onChange={e => {
                setStatusFilter(e.target.value);
              }}
            >
              <option value="ALL">All Status</option>
              <option value="UP">UP</option>
              <option value="DOWN">DOWN</option>
            </select>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-primary" onClick={() => handlePreview(1)} disabled={isLoading}>
              {isLoading ? 'Loading...' : 'Preview Data'}
            </button>
            <button className="btn btn-secondary" onClick={handleDownload} disabled={isLoading}>
              Download Excel
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '1rem', color: 'var(--text-color)' }}>Preview ({total} entries)</h3>
        {error && <div style={{ color: 'var(--danger-color)', marginBottom: '1rem' }}>{error}</div>}
        
        <table className="table-container">
          <thead>
            <tr>
              <th>Domain</th>
              <th>Current Status</th>
              <th>Incident Count</th>
              <th>Error Summary</th>
              <th>Total Downtime</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody style={{ opacity: isLoading ? 0.6 : 1, transition: 'opacity 0.2s' }}>
            {data.length === 0 && !isLoading ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '2rem' }}>No data to preview. Click "Preview Data".</td>
              </tr>
            ) : (
              data.map((row, idx) => (
                <tr key={idx}>
                  <td>
                    <strong>{row.domain_name}</strong>
                    <br/>
                    <small style={{ color: 'var(--text-secondary)' }}>{row.url}</small>
                  </td>
                  <td>
                    <Badge type={row.status === 'UP' ? 'success' : 'danger'}>{row.status}</Badge>
                  </td>
                  <td>{row.incident_count}</td>
                  <td>
                    <span style={{ fontSize: '0.9rem', color: row.incident_count > 0 ? 'var(--danger-color)' : 'inherit' }}>
                      {row.error_summary}
                    </span>
                  </td>
                  <td>{row.total_downtime}</td>
                  <td>{row.source}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {total > 0 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem', padding: '1rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>
              Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, total)} of {total} entries (Page {currentPage} of {totalPages})
            </span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                onClick={() => handlePreview(Math.max(1, currentPage - 1))} 
                disabled={currentPage === 1 || isLoading}
                className="btn btn-secondary"
                style={{ opacity: (currentPage === 1 || isLoading) ? 0.5 : 1 }}
              >
                Previous
              </button>
              <button 
                onClick={() => handlePreview(Math.min(totalPages, currentPage + 1))} 
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

export default Reports;
