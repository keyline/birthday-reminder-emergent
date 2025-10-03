import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { toast } from 'sonner';
import { 
  Users, 
  Shield, 
  TrendingUp, 
  Crown,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  UserPlus,
  Activity,
  Calendar,
  Trash2,
  Plus,
  Search,
  Filter,
  BarChart3,
  PieChart,
  Settings,
  AlertTriangle,
  Database,
  Mail,
  Phone,
  Coins,
  CreditCard,
  Infinity,
  MessageCircle
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminPage = () => {
  const [users, setUsers] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingUser, setUpdatingUser] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [isExtendDialogOpen, setIsExtendDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [extensionDays, setExtensionDays] = useState(30);
  const [customExpiryDate, setCustomExpiryDate] = useState('');
  const [isCreditDialogOpen, setIsCreditDialogOpen] = useState(false);
  const [selectedUserForCredits, setSelectedUserForCredits] = useState(null);
  const [creditUpdate, setCreditUpdate] = useState({
    whatsapp_credits: 0,
    email_credits: 0,
    unlimited_whatsapp: false,
    unlimited_email: false
  });
  
  // User credential management state
  const [isUserEditDialogOpen, setIsUserEditDialogOpen] = useState(false);
  const [selectedUserForEdit, setSelectedUserForEdit] = useState(null);
  const [userEditForm, setUserEditForm] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    password: ''
  });

  useEffect(() => {
    Promise.all([fetchDashboardStats(), fetchUsers()]);
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/platform-stats`);
      setDashboardStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      toast.error('Failed to load dashboard statistics');
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const updateUserSubscription = async (userId, newStatus) => {
    setUpdatingUser(userId);
    
    try {
      const response = await axios.put(`${API}/admin/users/${userId}`, {
        subscription_status: newStatus
      });
      
      toast.success(`User subscription updated to ${newStatus}!`);
      fetchUsers();
      fetchDashboardStats();
    } catch (error) {
      console.error('Error updating user subscription:', error);
      toast.error('Failed to update user subscription');
    } finally {
      setUpdatingUser(null);
    }
  };

  const updateUserExpiry = async (userId, expiryDate) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/expiry`, null, {
        params: { expiry_date: expiryDate }
      });
      
      toast.success('User expiry date updated successfully!');
      fetchUsers();
      setIsExtendDialogOpen(false);
      setSelectedUser(null);
    } catch (error) {
      console.error('Error updating user expiry:', error);
      toast.error('Failed to update expiry date');
    }
  };

  const extendUserSubscription = async (userId, days) => {
    try {
      const response = await axios.post(`${API}/admin/users/${userId}/extend`, null, {
        params: { days: days }
      });
      
      toast.success(`Subscription extended by ${days} days!`);
      fetchUsers();
      setIsExtendDialogOpen(false);
      setSelectedUser(null);
    } catch (error) {
      console.error('Error extending subscription:', error);
      toast.error('Failed to extend subscription');
    }
  };

  const updateUserCredits = async () => {
    try {
      await axios.put(`${API}/admin/users/${selectedUserForCredits.id}`, creditUpdate);
      toast.success('User credits updated successfully!');
      fetchUsers();
      setIsCreditDialogOpen(false);
      setSelectedUserForCredits(null);
      setCreditUpdate({
        whatsapp_credits: 0,
        email_credits: 0,
        unlimited_whatsapp: false,
        unlimited_email: false
      });
    } catch (error) {
      console.error('Error updating credits:', error);
      toast.error('Failed to update credits');
    }
  };

  const addCreditsToUser = async (userId, whatsappCredits, emailCredits) => {
    try {
      await axios.post(`${API}/admin/users/${userId}/add-credits`, null, {
        params: { 
          whatsapp_credits: whatsappCredits,
          email_credits: emailCredits
        }
      });
      
      toast.success(`Added ${whatsappCredits} WhatsApp and ${emailCredits} email credits!`);
      fetchUsers();
    } catch (error) {
      console.error('Error adding credits:', error);
      toast.error('Failed to add credits');
    }
  };

  // New user credential management functions
  const openUserEditDialog = (user) => {
    setSelectedUserForEdit(user);
    setUserEditForm({
      full_name: user.full_name || '',
      email: user.email || '',
      phone_number: user.phone_number || '',
      password: '' // Always empty for security
    });
    setIsUserEditDialogOpen(true);
  };

  const updateUserCredentials = async () => {
    try {
      // Only send fields that have values
      const updateData = {};
      if (userEditForm.full_name.trim()) updateData.full_name = userEditForm.full_name.trim();
      if (userEditForm.email.trim()) updateData.email = userEditForm.email.trim();
      if (userEditForm.phone_number.trim()) updateData.phone_number = userEditForm.phone_number.trim();
      if (userEditForm.password.trim()) updateData.password = userEditForm.password.trim();

      await axios.put(`${API}/admin/users/${selectedUserForEdit.id}`, updateData);
      
      toast.success('User credentials updated successfully!');
      fetchUsers();
      setIsUserEditDialogOpen(false);
      setSelectedUserForEdit(null);
      setUserEditForm({ full_name: '', email: '', phone_number: '', password: '' });
    } catch (error) {
      console.error('Error updating user credentials:', error);
      toast.error(error.response?.data?.detail || 'Failed to update user credentials');
    }
  };

  // deleteUser function is defined below to avoid duplicate

  const deleteUser = async (userId, userName) => {
    if (window.confirm(`Are you sure you want to delete ${userName}? This will permanently delete all their data including contacts and templates.`)) {
      try {
        await axios.delete(`${API}/admin/users/${userId}`);
        toast.success('User deleted successfully!');
        fetchUsers();
        fetchDashboardStats();
      } catch (error) {
        console.error('Error deleting user:', error);
        toast.error(error.response?.data?.detail || 'Failed to delete user');
      }
    }
  };

  const getSubscriptionColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'trial':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'expired':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'cancelled':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getSubscriptionIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'trial':
        return <Clock className="w-4 h-4 text-blue-500" />;
      case 'expired':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'cancelled':
        return <XCircle className="w-4 h-4 text-gray-500" />;
      default:
        return <Users className="w-4 h-4 text-gray-500" />;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not set';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric',
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isExpiringSoon = (expiryDate) => {
    if (!expiryDate) return false;
    const expiry = new Date(expiryDate);
    const today = new Date();
    const diffTime = expiry - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays <= 7 && diffDays > 0;
  };

  const isExpired = (expiryDate) => {
    if (!expiryDate) return false;
    const expiry = new Date(expiryDate);
    const today = new Date();
    return expiry < today;
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || user.subscription_status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const sortedUsers = filteredUsers.sort((a, b) => {
    // Sort by total usage (contacts + templates) descending
    return b.total_usage - a.total_usage;
  });

  if (loading) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" data-testid="admin-page">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center" data-testid="admin-title">
            <Shield className="w-8 h-8 mr-3 text-rose-500" />
            SaaS Admin Dashboard
          </h1>
          <p className="text-gray-600">
            Comprehensive user management and analytics for ReminderAI
          </p>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="users">User Management</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Dashboard Stats */}
            {dashboardStats && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="stats-card border-0 shadow-lg" data-testid="total-users-stat">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                      <Users className="w-4 h-4 mr-2 text-blue-500" />
                      Total Users
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="total-users-count">
                      {dashboardStats.total_users}
                    </div>
                    <p className="text-sm text-gray-600">
                      +{dashboardStats.recent_signups} this month
                    </p>
                  </CardContent>
                </Card>

                <Card className="stats-card border-0 shadow-lg" data-testid="active-users-stat">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                      <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                      Active Subscriptions
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="active-users-count">
                      {dashboardStats.active_subscriptions}
                    </div>
                    <p className="text-sm text-gray-600">
                      {((dashboardStats.active_subscriptions / dashboardStats.total_users) * 100).toFixed(1)}% conversion
                    </p>
                  </CardContent>
                </Card>

                <Card className="stats-card border-0 shadow-lg" data-testid="revenue-stat">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                      <DollarSign className="w-4 h-4 mr-2 text-green-500" />
                      Monthly Revenue
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="monthly-revenue">
                      ${dashboardStats.monthly_revenue.toFixed(2)}
                    </div>
                    <p className="text-sm text-gray-600">
                      ${(dashboardStats.monthly_revenue * 12).toFixed(0)} annual
                    </p>
                  </CardContent>
                </Card>

                <Card className="stats-card border-0 shadow-lg" data-testid="data-usage-stat">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                      <Database className="w-4 h-4 mr-2 text-purple-500" />
                      Platform Usage
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="total-contacts">
                      {dashboardStats.total_contacts}
                    </div>
                    <p className="text-sm text-gray-600">
                      {dashboardStats.total_templates} templates
                    </p>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Quick Stats */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="border-0 shadow-xl glass">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center">
                    <PieChart className="w-5 h-5 mr-2 text-rose-500" />
                    Subscription Breakdown
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {dashboardStats && (
                    <>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                          Active
                        </span>
                        <span className="font-semibold">{dashboardStats.active_subscriptions}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <Clock className="w-4 h-4 mr-2 text-blue-500" />
                          Trial
                        </span>
                        <span className="font-semibold">{dashboardStats.trial_users}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center">
                          <XCircle className="w-4 h-4 mr-2 text-red-500" />
                          Expired
                        </span>
                        <span className="font-semibold">{dashboardStats.expired_users}</span>
                      </div>
                      <div className="pt-2 border-t">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Churn Rate:</span>
                          <span className="font-semibold text-red-600">{dashboardStats.churn_rate.toFixed(1)}%</span>
                        </div>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card className="border-0 shadow-xl glass">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-rose-500" />
                    Growth Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {dashboardStats && (
                    <>
                      <div className="flex justify-between items-center">
                        <span>New Signups (30d):</span>
                        <span className="font-semibold text-green-600">+{dashboardStats.recent_signups}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Avg Revenue/User:</span>
                        <span className="font-semibold">
                          ${((dashboardStats.monthly_revenue / Math.max(dashboardStats.active_subscriptions, 1))).toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Avg Contacts/User:</span>
                        <span className="font-semibold">
                          {Math.round(dashboardStats.total_contacts / Math.max(dashboardStats.total_users, 1))}
                        </span>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card className="border-0 shadow-xl glass">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2 text-orange-500" />
                    Action Required
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {users.filter(u => isExpiringSoon(u.subscription_expires)).length > 0 && (
                    <Alert className="border-orange-200 bg-orange-50">
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                      <AlertDescription className="text-orange-800">
                        {users.filter(u => isExpiringSoon(u.subscription_expires)).length} subscriptions expiring soon
                      </AlertDescription>
                    </Alert>
                  )}
                  {users.filter(u => isExpired(u.subscription_expires)).length > 0 && (
                    <Alert className="border-red-200 bg-red-50">
                      <XCircle className="h-4 w-4 text-red-600" />
                      <AlertDescription className="text-red-800">
                        {users.filter(u => isExpired(u.subscription_expires)).length} subscriptions expired
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* User Management Tab */}
          <TabsContent value="users" className="space-y-6">
            {/* Search and Filter */}
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  data-testid="users-search-input"
                  placeholder="Search users by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-white/50"
                />
              </div>
              
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-full sm:w-[200px] bg-white/50" data-testid="users-filter-select">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="trial">Trial</SelectItem>
                  <SelectItem value="expired">Expired</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Users Management */}
            <Card className="border-0 shadow-xl glass" data-testid="users-management-card">
              <CardHeader>
                <CardTitle className="flex items-center text-xl">
                  <Crown className="w-5 h-5 mr-2 text-rose-500" />
                  User Management ({sortedUsers.length} users)
                </CardTitle>
                <CardDescription>
                  Comprehensive user management with subscription control and usage analytics
                </CardDescription>
              </CardHeader>
              <CardContent>
                {sortedUsers.length === 0 ? (
                  <div className="text-center py-12" data-testid="no-users-message">
                    <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No users found</h3>
                    <p className="text-gray-600">No users match your current search and filter criteria</p>
                  </div>
                ) : (
                  <div className="space-y-4" data-testid="users-list">
                    {sortedUsers.map((user) => (
                      <div 
                        key={user.id} 
                        className="flex items-center justify-between p-4 bg-white/50 rounded-lg border border-white/20 card-hover"
                        data-testid={`user-row-${user.id}`}
                      >
                        <div className="flex items-center space-x-4 flex-1">
                          <div className="flex-shrink-0">
                            <div className="w-12 h-12 bg-gradient-to-br from-rose-500 to-orange-400 rounded-full flex items-center justify-center">
                              <span className="text-white font-semibold text-lg">
                                {user.full_name?.charAt(0)?.toUpperCase() || 'U'}
                              </span>
                            </div>
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-1">
                              <h4 className="font-medium text-gray-900 truncate" data-testid={`user-name-${user.id}`}>
                                {user.full_name}
                              </h4>
                              {user.is_admin && (
                                <Badge variant="outline" className="bg-purple-100 text-purple-700 border-purple-200">
                                  <Shield className="w-3 h-3 mr-1" />
                                  Admin
                                </Badge>
                              )}
                              {isExpiringSoon(user.subscription_expires) && (
                                <Badge variant="outline" className="bg-orange-100 text-orange-700 border-orange-200">
                                  <AlertTriangle className="w-3 h-3 mr-1" />
                                  Expiring Soon
                                </Badge>
                              )}
                              {isExpired(user.subscription_expires) && (
                                <Badge variant="outline" className="bg-red-100 text-red-700 border-red-200">
                                  <XCircle className="w-3 h-3 mr-1" />
                                  Expired
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 truncate flex items-center" data-testid={`user-email-${user.id}`}>
                              <Mail className="w-3 h-3 mr-1" />
                              {user.email}
                            </p>
                            <div className="text-xs text-gray-500 mt-1 space-y-1">
                              <div>Joined: {formatDate(user.created_at)}</div>
                              {user.subscription_expires && (
                                <div className={isExpired(user.subscription_expires) ? 'text-red-600' : isExpiringSoon(user.subscription_expires) ? 'text-orange-600' : ''}>
                                  Expires: {formatDate(user.subscription_expires)}
                                </div>
                              )}
                            </div>
                          </div>

                          <div className="flex flex-col items-center space-y-2">
                            <Badge 
                              variant="outline" 
                              className={`${getSubscriptionColor(user.subscription_status)} font-medium flex items-center`}
                              data-testid={`user-status-${user.id}`}
                            >
                              {getSubscriptionIcon(user.subscription_status)}
                              <span className="ml-1 capitalize">{user.subscription_status}</span>
                            </Badge>
                            <div className="text-xs text-gray-500 text-center">
                              <div>{user.contacts_count} contacts</div>
                              <div>{user.templates_count} templates</div>
                            </div>
                            <div className="text-xs text-center space-y-1">
                              <div className="flex items-center justify-center space-x-1">
                                <MessageCircle className="w-3 h-3 text-green-600" />
                                <span className={user.unlimited_whatsapp ? 'text-green-600 font-medium' : ''}>
                                  {user.unlimited_whatsapp ? '∞' : user.whatsapp_credits}
                                </span>
                              </div>
                              <div className="flex items-center justify-center space-x-1">
                                <Mail className="w-3 h-3 text-blue-600" />
                                <span className={user.unlimited_email ? 'text-blue-600 font-medium' : ''}>
                                  {user.unlimited_email ? '∞' : user.email_credits}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-4">
                          <Select
                            value={user.subscription_status}
                            onValueChange={(value) => updateUserSubscription(user.id, value)}
                            disabled={updatingUser === user.id}
                          >
                            <SelectTrigger 
                              className="w-28" 
                              data-testid={`subscription-select-${user.id}`}
                            >
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="trial">Trial</SelectItem>
                              <SelectItem value="active">Active</SelectItem>
                              <SelectItem value="expired">Expired</SelectItem>
                              <SelectItem value="cancelled">Cancelled</SelectItem>
                            </SelectContent>
                          </Select>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedUser(user);
                              setIsExtendDialogOpen(true);
                            }}
                            data-testid={`extend-subscription-${user.id}`}
                          >
                            <Calendar className="w-4 h-4" />
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedUserForCredits(user);
                              setCreditUpdate({
                                whatsapp_credits: user.whatsapp_credits,
                                email_credits: user.email_credits,
                                unlimited_whatsapp: user.unlimited_whatsapp,
                                unlimited_email: user.unlimited_email
                              });
                              setIsCreditDialogOpen(true);
                            }}
                            className="text-green-600 hover:text-green-700 hover:bg-green-50"
                            data-testid={`manage-credits-${user.id}`}
                          >
                            <Coins className="w-4 h-4" />
                          </Button>
                          
                          {!user.is_admin && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => deleteUser(user.id, user.full_name)}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              data-testid={`delete-user-${user.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                          
                          {updatingUser === user.id && (
                            <div className="animate-spin rounded-full h-4 w-4 border-b border-rose-600" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="border-0 shadow-xl glass">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <BarChart3 className="w-5 h-5 mr-2 text-rose-500" />
                    User Distribution
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>Power Users (10+ contacts):</span>
                      <span className="font-semibold">
                        {users.filter(u => u.contacts_count >= 10).length}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Active Users (5+ contacts):</span>
                      <span className="font-semibold">
                        {users.filter(u => u.contacts_count >= 5).length}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Light Users (1-4 contacts):</span>
                      <span className="font-semibold">
                        {users.filter(u => u.contacts_count >= 1 && u.contacts_count < 5).length}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Inactive Users (0 contacts):</span>
                      <span className="font-semibold text-red-600">
                        {users.filter(u => u.contacts_count === 0).length}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-xl glass">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Activity className="w-5 h-5 mr-2 text-rose-500" />
                    Platform Health
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>Database Status:</span>
                      <Badge className="bg-green-100 text-green-700 border-green-200">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Healthy
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>API Status:</span>
                      <Badge className="bg-green-100 text-green-700 border-green-200">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Online
                      </Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>AI Service:</span>
                      <Badge className="bg-green-100 text-green-700 border-green-200">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Available
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <Card className="border-0 shadow-xl glass">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="w-5 h-5 mr-2 text-rose-500" />
                  System Settings
                </CardTitle>
                <CardDescription>
                  Configure platform-wide settings and preferences
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Alert>
                    <Settings className="h-4 w-4" />
                    <AlertDescription>
                      System settings will be implemented in future updates. Contact technical support for configuration changes.
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Credit Management Dialog */}
        <Dialog open={isCreditDialogOpen} onOpenChange={setIsCreditDialogOpen}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center">
                <Coins className="w-5 h-5 mr-2 text-green-600" />
                Manage Credits
              </DialogTitle>
              <DialogDescription>
                Manage credits for {selectedUserForCredits?.full_name}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-6">
              {/* WhatsApp Credits */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="flex items-center">
                    <MessageCircle className="w-4 h-4 mr-2 text-green-600" />
                    WhatsApp Credits
                  </Label>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={creditUpdate.unlimited_whatsapp}
                      onCheckedChange={(checked) => setCreditUpdate({
                        ...creditUpdate,
                        unlimited_whatsapp: checked
                      })}
                    />
                    <Label className="text-sm">Unlimited</Label>
                  </div>
                </div>
                {!creditUpdate.unlimited_whatsapp && (
                  <Input
                    type="number"
                    value={creditUpdate.whatsapp_credits}
                    onChange={(e) => setCreditUpdate({
                      ...creditUpdate,
                      whatsapp_credits: parseInt(e.target.value) || 0
                    })}
                    placeholder="WhatsApp credits"
                    min="0"
                  />
                )}
              </div>

              {/* Email Credits */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="flex items-center">
                    <Mail className="w-4 h-4 mr-2 text-blue-600" />
                    Email Credits
                  </Label>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={creditUpdate.unlimited_email}
                      onCheckedChange={(checked) => setCreditUpdate({
                        ...creditUpdate,
                        unlimited_email: checked
                      })}
                    />
                    <Label className="text-sm">Unlimited</Label>
                  </div>
                </div>
                {!creditUpdate.unlimited_email && (
                  <Input
                    type="number"
                    value={creditUpdate.email_credits}
                    onChange={(e) => setCreditUpdate({
                      ...creditUpdate,
                      email_credits: parseInt(e.target.value) || 0
                    })}
                    placeholder="Email credits"
                    min="0"
                  />
                )}
              </div>

              {/* Quick Actions */}
              <div className="space-y-2">
                <Label className="text-sm text-gray-600">Quick Add:</Label>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => addCreditsToUser(selectedUserForCredits?.id, 100, 100)}
                  >
                    +100 Both
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => addCreditsToUser(selectedUserForCredits?.id, 500, 500)}
                  >
                    +500 Both
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => addCreditsToUser(selectedUserForCredits?.id, 1000, 1000)}
                  >
                    +1000 Both
                  </Button>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setIsCreditDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={updateUserCredits}
                  className="btn-gradient"
                >
                  Update Credits
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Extend Subscription Dialog */}
        <Dialog open={isExtendDialogOpen} onOpenChange={setIsExtendDialogOpen}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Extend Subscription</DialogTitle>
              <DialogDescription>
                Manage subscription for {selectedUser?.full_name}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Extend by Days</Label>
                <Input
                  type="number"
                  value={extensionDays}
                  onChange={(e) => setExtensionDays(parseInt(e.target.value) || 0)}
                  placeholder="Enter number of days"
                />
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setExtensionDays(7)}
                  >
                    7 days
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setExtensionDays(30)}
                  >
                    30 days
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"  
                    onClick={() => setExtensionDays(90)}
                  >
                    90 days
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Or Set Custom Expiry Date</Label>
                <Input
                  type="datetime-local"
                  value={customExpiryDate}
                  onChange={(e) => setCustomExpiryDate(e.target.value)}
                />
              </div>
              
              <div className="flex justify-end space-x-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setIsExtendDialogOpen(false)}
                >
                  Cancel
                </Button>
                {customExpiryDate ? (
                  <Button
                    onClick={() => updateUserExpiry(selectedUser?.id, customExpiryDate)}
                    className="btn-gradient"
                  >
                    Set Expiry Date
                  </Button>
                ) : (
                  <Button
                    onClick={() => extendUserSubscription(selectedUser?.id, extensionDays)}
                    className="btn-gradient"
                  >
                    Extend by {extensionDays} days
                  </Button>
                )}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AdminPage;