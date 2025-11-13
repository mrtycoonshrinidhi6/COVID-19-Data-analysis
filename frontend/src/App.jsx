import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import axios from 'axios'
import { AnimatedCounter } from './components/AnimatedCounter'
import './App.css'

const API_BASE = 'http://localhost:8000/api/v1'

function App() {
  const [countries, setCountries] = useState([])
  const [selectedCountry, setSelectedCountry] = useState('USA')
  const [timeseriesData, setTimeseriesData] = useState([])
  const [globalSummary, setGlobalSummary] = useState(null)
  const [countrySummary, setCountrySummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Fetch countries on mount
  useEffect(() => {
    fetchCountries()
    fetchGlobalSummary()
  }, [])

  // Fetch timeseries when country changes
  useEffect(() => {
    if (selectedCountry) {
      fetchTimeseries(selectedCountry)
    }
  }, [selectedCountry])

  const fetchCountries = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE}/countries`)
      setCountries(response.data)
      setError('')
    } catch (err) {
      setError(`Failed to load countries: ${err.message}`)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchGlobalSummary = async () => {
    try {
      const response = await axios.get(`${API_BASE}/summary`)
      setGlobalSummary(response.data)
    } catch (err) {
      console.error('Failed to load global summary:', err)
    }
  }

  const fetchTimeseries = async (iso3) => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE}/countries/${iso3}/timeseries`)
      setTimeseriesData(response.data.data || [])
      setError('')
    } catch (err) {
      setError(`Failed to load timeseries: ${err.message}`)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Calculate country summary from timeseries data
  const calculateCountrySummary = (data, countryName) => {
    if (!data || data.length === 0) return null
    
    const lastEntry = data[data.length - 1]
    const firstEntry = data[0]
    
    return {
      country: countryName,
      date: lastEntry.date,
      total_confirmed_cases: lastEntry.confirmed_cases || 0,
      total_deaths: lastEntry.deaths || 0,
      total_vaccinations: lastEntry.total_vaccinations || 0,
      people_fully_vaccinated: lastEntry.people_fully_vaccinated || 0,
      new_cases: (lastEntry.confirmed_cases || 0) - (firstEntry.confirmed_cases || 0),
      new_deaths: (lastEntry.deaths || 0) - (firstEntry.deaths || 0)
    }
  }

  // Update country summary when timeseries changes
  useEffect(() => {
    if (timeseriesData.length > 0) {
      const countryName = countries.find(c => c.iso3 === selectedCountry)?.name || selectedCountry
      const summary = calculateCountrySummary(timeseriesData, countryName)
      setCountrySummary(summary)
    } else {
      setCountrySummary(null)
    }
  }, [timeseriesData, selectedCountry, countries])

  // Calculate rolling average (7-day)
  const calculateRollingAverage = (data, field, window = 7) => {
    return data.map((item, idx) => {
      const start = Math.max(0, idx - window + 1)
      const subset = data.slice(start, idx + 1)
      const values = subset.map(d => d[field]).filter(v => v !== null)
      const avg = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : null
      return { ...item, [field + '_7day']: avg }
    })
  }

  const enhancedData = calculateRollingAverage(timeseriesData, 'confirmed_cases')

  return (
    <div className="app">
      <header className="app-header">
        <h1>🦠 COVID-19 Data Dashboard</h1>
        <p>Global pandemic tracking with timeseries analysis</p>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <main className="app-main">
      {/* Global Summary */}
      <section className="summary-section">
        <h2>Global Summary</h2>
        {globalSummary && (
          <motion.div 
            className="summary-cards"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, staggerChildren: 0.1 }}
          >
            <motion.div 
              className="summary-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              whileHover={{ scale: 1.05, boxShadow: '0 8px 16px rgba(0,0,0,0.3)' }}
            >
              <span className="label">Total Cases</span>
              <span className="value"><AnimatedCounter to={globalSummary.total_confirmed_cases} duration={2.5} /></span>
              <span className="date">as of {globalSummary.date}</span>
            </motion.div>
            <motion.div 
              className="summary-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              whileHover={{ scale: 1.05, boxShadow: '0 8px 16px rgba(255,107,107,0.3)' }}
            >
              <span className="label">Total Deaths</span>
              <span className="value" style={{color: '#ff6b6b'}}><AnimatedCounter to={globalSummary.total_deaths} duration={2.5} /></span>
            </motion.div>
            <motion.div 
              className="summary-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              whileHover={{ scale: 1.05, boxShadow: '0 8px 16px rgba(78,205,196,0.3)' }}
            >
              <span className="label">Countries Affected</span>
              <span className="value" style={{color: '#4ecdc4'}}><AnimatedCounter to={globalSummary.countries_affected} duration={1.5} /></span>
            </motion.div>
            <motion.div 
              className="summary-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              whileHover={{ scale: 1.05, boxShadow: '0 8px 16px rgba(149,225,211,0.3)' }}
            >
              <span className="label">Total Vaccinations</span>
              <span className="value" style={{color: '#95e1d3'}}><AnimatedCounter to={globalSummary.total_vaccinations || 0} duration={2.5} /></span>
            </motion.div>
            <motion.div 
              className="summary-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              whileHover={{ scale: 1.05, boxShadow: '0 8px 16px rgba(126,211,193,0.3)' }}
            >
              <span className="label">Fully Vaccinated</span>
              <span className="value" style={{color: '#7ed3c1'}}><AnimatedCounter to={globalSummary.people_fully_vaccinated || 0} duration={2.5} /></span>
            </motion.div>
          </motion.div>
        )}
      </section>        {/* Country Summary */}
        {countrySummary && (
        <section className="summary-section">
          <h2>📍 {countrySummary.country} Summary</h2>
          <motion.div 
            className="summary-cards"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, staggerChildren: 0.1 }}
          >
            <motion.div 
              className="summary-card country-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              whileHover={{ scale: 1.05, boxShadow: '0 8px 16px rgba(0,0,0,0.3)' }}
            >
              <span className="label">Total Cases</span>
              <span className="value"><AnimatedCounter to={countrySummary.total_confirmed_cases} duration={2.5} /></span>
              <span className="date">as of {countrySummary.date}</span>
            </motion.div>
            <motion.div 
              className="summary-card country-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              whileHover={{ scale: 1.05, boxShadow: '0 8px 16px rgba(255,107,107,0.3)' }}
            >
              <span className="label">Total Deaths</span>
              <span className="value" style={{color: '#ff6b6b'}}><AnimatedCounter to={countrySummary.total_deaths} duration={2.5} /></span>
            </motion.div>
            <motion.div 
              className="summary-card country-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              whileHover={{ scale: 1.05, boxShadow: '0 8px 16px rgba(78,205,196,0.3)' }}
            >
              <span className="label">Total Vaccinations</span>
              <span className="value" style={{color: '#95e1d3'}}><AnimatedCounter to={countrySummary.total_vaccinations} duration={2.5} /></span>
            </motion.div>
            <motion.div 
              className="summary-card country-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              whileHover={{ scale: 1.05, boxShadow: '0 8px 16px rgba(149,225,211,0.3)' }}
            >
              <span className="label">Fully Vaccinated</span>
              <span className="value" style={{color: '#7ed3c1'}}><AnimatedCounter to={countrySummary.people_fully_vaccinated} duration={2.5} /></span>
            </motion.div>
          </motion.div>
        </section>
        )}

        {/* Country Selection & Timeseries */}
        <section className="timeseries-section">
          <h2>Country Analysis</h2>
          
          <motion.div 
            className="controls"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4 }}
          >
            <label>Select Country:</label>
            <select 
              value={selectedCountry} 
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="country-select"
            >
              {countries.map(c => (
                <option key={c.iso3} value={c.iso3}>{c.name}</option>
              ))}
            </select>
          </motion.div>

          {loading && <motion.p className="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>Loading data...</motion.p>}

          {timeseriesData.length > 0 && (
            <motion.div 
              className="charts-container"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, staggerChildren: 0.1 }}
            >
              {/* Cases Chart */}
              <motion.div 
                className="chart-wrapper"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
              >
                <h3>Confirmed Cases</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={enhancedData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis dataKey="date" stroke="#999" />
                    <YAxis stroke="#999" />
                    <Tooltip 
                      contentStyle={{backgroundColor: '#1a1a1a', border: '1px solid #444'}}
                      formatter={(value) => value ? value.toLocaleString() : 'N/A'}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="confirmed_cases" 
                      stroke="#8884d8" 
                      dot={false}
                      name="Cases"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="confirmed_cases_7day" 
                      stroke="#ffc658" 
                      dot={false}
                      name="7-Day Average"
                      strokeDasharray="5 5"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </motion.div>

              {/* Deaths Chart */}
              <motion.div 
                className="chart-wrapper"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 }}
              >
                <h3>Cumulative Deaths</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={timeseriesData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis dataKey="date" stroke="#999" />
                    <YAxis stroke="#999" />
                    <Tooltip 
                      contentStyle={{backgroundColor: '#1a1a1a', border: '1px solid #444'}}
                      formatter={(value) => value ? value.toLocaleString() : 'N/A'}
                    />
                    <Bar dataKey="deaths" fill="#ff6b6b" name="Deaths" />
                  </BarChart>
                </ResponsiveContainer>
              </motion.div>

              {/* Vaccinations Chart */}
              {timeseriesData.some(d => d.total_vaccinations) && (
                <motion.div 
                  className="chart-wrapper"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.2 }}
                >
                  <h3>Total Vaccinations</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={timeseriesData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                      <XAxis dataKey="date" stroke="#999" />
                      <YAxis stroke="#999" />
                      <Tooltip 
                        contentStyle={{backgroundColor: '#1a1a1a', border: '1px solid #444'}}
                        formatter={(value) => value ? value.toLocaleString() : 'N/A'}
                      />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="total_vaccinations" 
                        stroke="#95e1d3" 
                        dot={false}
                        name="Total Vaccinations"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="people_fully_vaccinated" 
                        stroke="#4ecdc4" 
                        dot={false}
                        name="Fully Vaccinated"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </motion.div>
              )}
            </motion.div>
          )}
        </section>

        {/* Data Table */}
        {timeseriesData.length > 0 && (
          <motion.section 
            className="table-section"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <h2>Detailed Data</h2>
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Cases</th>
                    <th>Deaths</th>
                    <th>Vaccinations</th>
                    <th>Fully Vaccinated</th>
                  </tr>
                </thead>
                <tbody>
                  {timeseriesData.slice(-30).reverse().map((row, idx) => (
                    <motion.tr 
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: idx * 0.02 }}
                      whileHover={{ backgroundColor: 'rgba(0,0,0,0.3)' }}
                    >
                      <td>{row.date}</td>
                      <td>{row.confirmed_cases ? row.confirmed_cases.toLocaleString() : '—'}</td>
                      <td>{row.deaths ? row.deaths.toLocaleString() : '—'}</td>
                      <td>{row.total_vaccinations ? row.total_vaccinations.toLocaleString() : '—'}</td>
                      <td>{row.people_fully_vaccinated ? row.people_fully_vaccinated.toLocaleString() : '—'}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.section>
        )}
      </main>

      <footer className="app-footer">
        <p>Built with React and Recharts • Data from OWID & Johns Hopkins</p>
      </footer>
    </div>
  )
}

export default App
