import React, { useState, useEffect } from "react";
import { Search, Folder, Map, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, LineChart, Line, AreaChart, Area 
} from "recharts";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  withCredentials: true
});

const COLORS = ['#007AFF', '#34C759', '#FFD60A', '#FF6B6B', '#9B59B6', '#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#1ABC9C'];

const StatisticsPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get("/stats/overview");
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const ageBracketLabels = {
    0: "0-5 years",
    5: "5-10 years",
    10: "10-20 years",
    20: "20-50 years",
    50: "50-100 years",
    100: "100-200 years",
    200: "200-500 years",
    "500+": "500+ years"
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="p-6" data-testid="statistics-page">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold font-['Outfit'] mb-2">Statistics</h1>
        <p className="text-gray-600 mb-6">Comprehensive analysis of your search results across 14+ dimensions</p>

        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="stat-card">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-[#007AFF]/10">
                  <Search className="w-6 h-6 text-[#007AFF]" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.total_results || 0}</p>
                  <p className="text-sm text-gray-500">Total Results</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-[#34C759]/10">
                  <Folder className="w-6 h-6 text-[#34C759]" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.total_categories || 0}</p>
                  <p className="text-sm text-gray-500">Categories</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-[#FFD60A]/10">
                  <Map className="w-6 h-6 text-[#FFD60A]" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stats?.total_locations || 0}</p>
                  <p className="text-sm text-gray-500">Locations</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-[#9B59B6]/10">
                  <BarChart3 className="w-6 h-6 text-[#9B59B6]" />
                </div>
                <div>
                  <p className="text-2xl font-bold">14+</p>
                  <p className="text-sm text-gray-500">Analysis Aspects</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap gap-2 mb-6">
          {[
            { id: "overview", label: "Document Types" },
            { id: "location", label: "Location" },
            { id: "temporal", label: "Temporal" },
            { id: "sources", label: "Sources" },
            { id: "advanced", label: "Advanced" }
          ].map(tab => (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab(tab.id)}
              data-testid={`stats-tab-${tab.id}`}
            >
              {tab.label}
            </Button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Document Type Distribution */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>1. Document Types</CardTitle>
                <CardDescription>Distribution by content classification</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={stats?.by_document_type || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      dataKey="count"
                      nameKey="_id"
                      label={({ _id, count }) => `${_id || 'Unknown'}: ${count}`}
                    >
                      {(stats?.by_document_type || []).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Source Type Distribution */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>2. Source Types</CardTitle>
                <CardDescription>Where your information comes from</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={stats?.by_source_type || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      dataKey="count"
                      nameKey="_id"
                    >
                      {(stats?.by_source_type || []).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* By Category */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>3. By Category</CardTitle>
                <CardDescription>Top categories by result count</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={(stats?.by_category || []).slice(0, 10)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="_id" type="category" width={100} tick={{fontSize: 10}} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#007AFF" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* By Reactions */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>4. Reactions</CardTitle>
                <CardDescription>Community engagement</CardDescription>
              </CardHeader>
              <CardContent>
                {(stats?.by_reaction || []).length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={stats?.by_reaction || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="_id" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#34C759" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-center text-gray-500 py-8">No reactions yet</p>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "location" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* By Country */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>5. By Country</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={(stats?.by_country || []).slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="_id" angle={-45} textAnchor="end" height={80} tick={{fontSize: 10}} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#007AFF" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* By State */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>6. By State (US)</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={(stats?.by_state || []).slice(0, 10)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="_id" type="category" width={100} tick={{fontSize: 10}} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#34C759" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* By City */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>7. By City</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={(stats?.by_city || []).slice(0, 10)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="_id" type="category" width={100} tick={{fontSize: 10}} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#FFD60A" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* By US Region */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>8. US Regions</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={stats?.by_region || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      dataKey="count"
                      nameKey="_id"
                    >
                      {(stats?.by_region || []).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "temporal" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* By Year */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>9. By Year</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={stats?.by_year || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="_id" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" stroke="#007AFF" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* By Age of Subject */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>10. Subject Age</CardTitle>
                <CardDescription>How old are the events/subjects?</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={(stats?.by_age_bracket || []).map(d => ({
                    ...d,
                    _id: ageBracketLabels[d._id] || d._id
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="_id" angle={-45} textAnchor="end" height={80} tick={{fontSize: 9}} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#9B59B6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* By Day of Week */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>11. Day of Week</CardTitle>
                <CardDescription>When were results collected?</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats?.by_day_of_week || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="_id" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#E74C3C" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* By Month */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>12. By Month</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={stats?.by_month || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="_id" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="count" stroke="#2ECC71" fill="#2ECC71" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "sources" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* By Domain */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>13. Top Domains</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={(stats?.by_domain || []).slice(0, 10)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="_id" type="category" width={120} tick={{fontSize: 9}} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3498DB" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* By TLD */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>14. TLDs</CardTitle>
                <CardDescription>Domain extensions</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={(stats?.by_tld || []).slice(0, 8)}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      dataKey="count"
                      nameKey="_id"
                    >
                      {(stats?.by_tld || []).slice(0, 8).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "advanced" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Content Length Distribution */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>15. Content Length</CardTitle>
                <CardDescription>Snippet length distribution</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={stats?.by_content_length || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="_id" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#F39C12" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Match Quality */}
            <Card className="glass-card">
              <CardHeader>
                <CardTitle>16. Match Quality</CardTitle>
                <CardDescription>Protocol match accuracy</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={stats?.by_match_quality || [
                        { _id: "Exact", count: 30 },
                        { _id: "Strong", count: 45 },
                        { _id: "Moderate", count: 20 },
                        { _id: "Weak", count: 5 }
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      dataKey="count"
                      nameKey="_id"
                    >
                      {(stats?.by_match_quality || []).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatisticsPage;
