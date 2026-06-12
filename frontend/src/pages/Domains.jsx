import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Plus, Trash2, Upload, Download, ArrowUpDown, ArrowUp, ArrowDown, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import client from '../api/client';
import Badge from '../components/UI/Badge';

const Domains = () => {
  const [domains, setDomains] = useState([]);
  const [url, setUrl] = useState('');
  const [name, setName] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const fileInputRef = useRef(null);

  // Filter & Sort State
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [filterSSL, setFilterSSL] = useState('ALL');
  const [filterSearch, setFilterSearch] = useState('');
  const [sortField, setSortField] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc'); // 'asc' | 'desc'
  
  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10); // 10, 20, 50, 100, 'ALL'

  useEffect(() => {
    fetchDomains();
  }, []);

  const fetchDomains = async () => {
    try {
      const res = await client.get('/domains/');
      setDomains(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!url || !name) return;
    try {
      await client.post('/domains/', { url, name, is_active: true });
      setUrl('');
      setName('');
      fetchDomains();
    } catch (err) {
      alert("Failed to add domain. URL might exist.");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure?")) return;
    try {
      await client.delete(`/domains/${id}`);
      fetchDomains();
    } catch (err) {
      console.error(err);
    }
  };

  const handleBulkDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete ${selectedIds.length} domains?`)) return;
    try {
      await client.post('/domains/bulk-delete', { ids: selectedIds });
      setSelectedIds([]);
      fetchDomains();
    } catch (err) {
      console.error(err);
      alert("Failed to delete selected domains.");
    }
  };

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsImporting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await client.post('/domains/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert(`Import success: ${res.data.imported} domains imported.`);
      fetchDomains();
    } catch (err) {
      console.error(err);
      alert('Failed to import domains. ' + (err.response?.data?.detail || ''));
    } finally {
      setIsImporting(false);
      e.target.value = null;
    }
  };

  const handleExport = () => {
    try {
      const csvRows = [];
      csvRows.push(['ID', 'Name', 'URL', 'Status', 'Error Classification', 'SSL'].join(','));
      
      processedDomains.forEach((d, i) => {
        csvRows.push([
          i + 1,
          `"${(d.name || '').replace(/"/g, '""')}"`,
          `"${d.url || ''}"`,
          `"${d.status || ''}"`,
          `"${(d.error_info || '').replace(/"/g, '""')}"`,
          `"${d.ssl_info || ''}"`
        ].join(','));
      });
      
      const csvContent = csvRows.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', 'domains_filtered.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
      alert('Failed to export domains.');
    }
  };

  const downloadTemplate = () => {
    const csvContent = "name,url,is_active\nExample App,https://example.com,true\n";
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const urlBlob = URL.createObjectURL(blob);
    link.setAttribute("href", urlBlob);
    link.setAttribute("download", "domain_template.csv");
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // --- Filtering and Sorting Logic ---
  const processedDomains = useMemo(() => {
    let result = [...domains];

    // Search filter
    if (filterSearch) {
      const lowerSearch = filterSearch.toLowerCase();
      result = result.filter(d => 
        (d.name && d.name.toLowerCase().includes(lowerSearch)) || 
        (d.url && d.url.toLowerCase().includes(lowerSearch))
      );
    }

    // Status filter
    if (filterStatus !== 'ALL') {
      result = result.filter(d => d.status === filterStatus);
    }

    // SSL filter
    if (filterSSL !== 'ALL') {
      result = result.filter(d => {
        const ssl = d.ssl_info || 'N/A';
        if (filterSSL === 'VALID') return ssl.startsWith('Valid');
        if (filterSSL === 'WARNING') return ssl.startsWith('Warning');
        if (filterSSL === 'EXPIRED') return ssl === 'Expired';
        if (filterSSL === 'N/A') return ssl === 'N/A';
        return true;
      });
    }

    // Sorting
    result.sort((a, b) => {
      let aVal = a[sortField] || '';
      let bVal = b[sortField] || '';
      
      if (sortField === 'ssl_info') {
        aVal = a.ssl_info || 'N/A';
        bVal = b.ssl_info || 'N/A';
      }

      if (typeof aVal === 'string') aVal = aVal.toLowerCase();
      if (typeof bVal === 'string') bVal = bVal.toLowerCase();

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [domains, filterSearch, filterStatus, filterSSL, sortField, sortOrder]);

  // --- Pagination Logic ---
  const totalPages = itemsPerPage === 'ALL' ? 1 : Math.ceil(processedDomains.length / itemsPerPage);
  
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(1);
    }
  }, [totalPages, currentPage, processedDomains.length]);

  const displayedDomains = useMemo(() => {
    if (itemsPerPage === 'ALL') return processedDomains;
    const start = (currentPage - 1) * itemsPerPage;
    return processedDomains.slice(start, start + itemsPerPage);
  }, [processedDomains, currentPage, itemsPerPage]);

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const renderSortIcon = (field) => {
    if (sortField !== field) return <ArrowUpDown size={14} style={{ opacity: 0.3, marginLeft: 4, cursor: 'pointer' }} onClick={() => toggleSort(field)} />;
    return sortOrder === 'asc' 
      ? <ArrowUp size={14} style={{ marginLeft: 4, cursor: 'pointer', color: '#3b82f6' }} onClick={() => toggleSort(field)} /> 
      : <ArrowDown size={14} style={{ marginLeft: 4, cursor: 'pointer', color: '#3b82f6' }} onClick={() => toggleSort(field)} />;
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(displayedDomains.map(d => d.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (id) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(selectedId => selectedId !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <h1>Domain Management</h1>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {selectedIds.length > 0 && (
            <button className="btn outline danger" onClick={handleBulkDelete}>
              <Trash2 size={18} /> Delete Selected ({selectedIds.length})
            </button>
          )}
          <button className="btn outline" onClick={downloadTemplate} title="Download CSV Template">
            Template
          </button>
          <input type="file" ref={fileInputRef} onChange={handleImport} accept=".csv, .xlsx" style={{ display: 'none' }} />
          <button className="btn outline" onClick={() => fileInputRef.current.click()} disabled={isImporting}>
            <Upload size={18} /> {isImporting ? 'Importing...' : 'Import'}
          </button>
          <button className="btn outline" onClick={handleExport}>
            <Download size={18} /> Export
          </button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Add New Target</h3>
        <form onSubmit={handleAdd} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ marginBottom: 0, flex: 1, minWidth: '200px' }}>
            <label>Domain URL</label>
            <input type="url" value={url} onChange={e => setUrl(e.target.value)} placeholder="https://example.com" required />
          </div>
          <div className="form-group" style={{ marginBottom: 0, flex: 1, minWidth: '200px' }}>
            <label>Name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Example Web" required />
          </div>
          <button type="submit" className="btn" style={{ whiteSpace: 'nowrap' }}><Plus size={18} /> Add Target</button>
        </form>
      </div>

      {/* Filter Options */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Search size={18} style={{ color: '#6b7280' }}/>
            <input 
              type="text" 
              placeholder="Search domains..." 
              value={filterSearch}
              onChange={e => setFilterSearch(e.target.value)}
              style={{ padding: '0.4rem 0.8rem', borderRadius: '4px', border: '1px solid #e5e7eb', outline: 'none', minWidth: '200px' }}
            />
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 600, color: '#374151' }}>Status:</label>
            <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #e5e7eb' }}>
              <option value="ALL">All Status</option>
              <option value="UP">UP</option>
              <option value="DOWN">DOWN</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 600, color: '#374151' }}>SSL:</label>
            <select value={filterSSL} onChange={e => setFilterSSL(e.target.value)} style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #e5e7eb' }}>
              <option value="ALL">All SSL</option>
              <option value="VALID">Valid</option>
              <option value="WARNING">Warning</option>
              <option value="EXPIRED">Expired</option>
              <option value="N/A">N/A</option>
            </select>
          </div>

          <div style={{ marginLeft: 'auto', fontSize: '0.875rem', color: '#6b7280' }}>
            Showing {displayedDomains.length} of {processedDomains.length} domains
          </div>
        </div>
      </div>

      <div className="card">
        <div style={{ overflowX: 'auto' }}>
          <table className="table-container">
            <thead>
              <tr>
                <th style={{ width: '40px' }}>
                  <input 
                    type="checkbox" 
                    onChange={handleSelectAll} 
                    checked={displayedDomains.length > 0 && selectedIds.length === displayedDomains.length} 
                  />
                </th>
                <th>ID</th>
                <th style={{ cursor: 'pointer', whiteSpace: 'nowrap', userSelect: 'none' }} onClick={() => toggleSort('name')}>
                  <div style={{ display: 'flex', alignItems: 'center' }}>Name {renderSortIcon('name')}</div>
                </th>
                <th style={{ cursor: 'pointer', whiteSpace: 'nowrap', userSelect: 'none' }} onClick={() => toggleSort('url')}>
                  <div style={{ display: 'flex', alignItems: 'center' }}>URL {renderSortIcon('url')}</div>
                </th>
                <th>Monitoring</th>
                <th style={{ cursor: 'pointer', whiteSpace: 'nowrap', userSelect: 'none' }} onClick={() => toggleSort('status')}>
                  <div style={{ display: 'flex', alignItems: 'center' }}>Status {renderSortIcon('status')}</div>
                </th>
                <th>Error Classification</th>
                <th style={{ cursor: 'pointer', whiteSpace: 'nowrap', userSelect: 'none' }} onClick={() => toggleSort('ssl_info')}>
                  <div style={{ display: 'flex', alignItems: 'center' }}>SSL {renderSortIcon('ssl_info')}</div>
                </th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {displayedDomains.length === 0 ? (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>No domains found.</td>
                </tr>
              ) : (
                displayedDomains.map((d, index) => {
                  // Calculate absolute ID based on pagination for display
                  const displayId = itemsPerPage === 'ALL' ? index + 1 : (currentPage - 1) * itemsPerPage + index + 1;
                  return (
                    <tr key={d.id}>
                      <td>
                        <input type="checkbox" onChange={() => handleSelectOne(d.id)} checked={selectedIds.includes(d.id)} />
                      </td>
                      <td>{displayId}</td>
                      <td style={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={d.name}>{d.name}</td>
                      <td style={{ wordBreak: 'break-all', minWidth: '200px' }}><a href={d.url} target="_blank" rel="noreferrer">{d.url}</a></td>
                      <td><Badge type={d.is_active ? 'info' : 'warning'}>{d.is_active ? 'On' : 'Off'}</Badge></td>
                      <td>
                        <Badge type={d.status === 'UP' ? 'success' : (d.status === 'DOWN' ? 'danger' : 'warning')}>
                          {d.status}
                        </Badge>
                      </td>
                      <td style={{ maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', whiteSpace: 'normal' }} title={d.error_info}>
                        {d.error_info ? <span style={{ color: '#ef4444', fontSize: '0.75rem', lineHeight: '1.2' }}>{d.error_info}</span> : <span style={{ color: '#9ca3af', fontSize: '0.875rem' }}>-</span>}
                      </td>
                      <td>
                        <Badge type={d.ssl_info?.startsWith('Valid') ? 'success' : (d.ssl_info?.startsWith('Warning') ? 'warning' : (d.ssl_info === 'Expired' ? 'danger' : 'default'))}>
                          {d.ssl_info || 'N/A'}
                        </Badge>
                      </td>
                      <td>
                        <button onClick={() => handleDelete(d.id)} className="btn outline danger" style={{ padding: '0.4rem' }}>
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Controls */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem', padding: '0 0.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.875rem', color: '#4b5563' }}>Rows per page:</span>
            <select 
              value={itemsPerPage} 
              onChange={e => {
                const val = e.target.value === 'ALL' ? 'ALL' : Number(e.target.value);
                setItemsPerPage(val);
                setCurrentPage(1);
              }}
              style={{ padding: '0.3rem', borderRadius: '4px', border: '1px solid #e5e7eb', outline: 'none' }}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value="ALL">All</option>
            </select>
          </div>
          
          {itemsPerPage !== 'ALL' && totalPages > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span style={{ fontSize: '0.875rem', color: '#4b5563' }}>
                Page {currentPage} of {totalPages}
              </span>
              <div style={{ display: 'flex', gap: '0.25rem' }}>
                <button 
                  className="btn outline" 
                  style={{ padding: '0.4rem' }} 
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft size={16} />
                </button>
                <button 
                  className="btn outline" 
                  style={{ padding: '0.4rem' }} 
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Domains;
