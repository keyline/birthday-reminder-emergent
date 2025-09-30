import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { 
  Calendar, 
  Users, 
  FileText, 
  Gift, 
  Heart, 
  Plus,
  Clock,
  Sparkles,
  TrendingUp,
  MessageCircle,
  Mail,
  Coins,
  Infinity
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    total_contacts: 0,
    total_templates: 0,
    upcoming_events: []
  });
  const [credits, setCredits] = useState({
    whatsapp_credits: 0,
    email_credits: 0,
    unlimited_whatsapp: false,
    unlimited_email: false
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
    fetchCredits();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const fetchCredits = async () => {
    try {
      const response = await axios.get(`${API}/credits`);
      setCredits(response.data);
    } catch (error) {
      console.error('Error fetching credits:', error);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const getDaysUntilText = (days) => {
    if (days === 0) return 'Today!';
    if (days === 1) return 'Tomorrow';
    return `${days} days`;
  };

  const getEventIcon = (eventType) => {
    return eventType === 'birthday' ? (
      <Gift className="w-4 h-4 text-rose-500" />
    ) : (
      <Heart className="w-4 h-4 text-pink-500" />
    );
  };

  const getEventColor = (eventType) => {
    return eventType === 'birthday' 
      ? 'bg-rose-100 text-rose-700 border-rose-200'
      : 'bg-pink-100 text-pink-700 border-pink-200';
  };

  if (loading) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" data-testid="dashboard">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2" data-testid="dashboard-title">
            Welcome back, {user?.full_name?.split(' ')[0]}! 👋
          </h1>
          <p className="text-gray-600">
            Here's what's coming up and how your reminders are doing.
          </p>
        </div>

        {/* Credits Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <Card className="stats-card border-0 shadow-lg bg-gradient-to-r from-green-50 to-emerald-50" data-testid="whatsapp-credits-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-700 flex items-center">
                <MessageCircle className="w-4 h-4 mr-2 text-green-500" />
                WhatsApp Credits
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-1 flex items-center" data-testid="whatsapp-credits-count">
                {credits.unlimited_whatsapp ? (
                  <>
                    <Infinity className="w-8 h-8 text-green-600 mr-2" />
                    <span className="text-green-600">Unlimited</span>
                  </>
                ) : (
                  <>
                    {credits.whatsapp_credits}
                    <Coins className="w-6 h-6 text-green-600 ml-2" />
                  </>
                )}
              </div>
              <p className="text-sm text-gray-600">Messages remaining</p>
            </CardContent>
          </Card>

          <Card className="stats-card border-0 shadow-lg bg-gradient-to-r from-blue-50 to-cyan-50" data-testid="email-credits-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-700 flex items-center">
                <Mail className="w-4 h-4 mr-2 text-blue-500" />
                Email Credits
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-1 flex items-center" data-testid="email-credits-count">
                {credits.unlimited_email ? (
                  <>
                    <Infinity className="w-8 h-8 text-blue-600 mr-2" />
                    <span className="text-blue-600">Unlimited</span>
                  </>
                ) : (
                  <>
                    {credits.email_credits}
                    <Coins className="w-6 h-6 text-blue-600 ml-2" />
                  </>
                )}
              </div>
              <p className="text-sm text-gray-600">Messages remaining</p>
            </CardContent>
          </Card>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="stats-card border-0 shadow-lg" data-testid="contacts-stat-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <Users className="w-4 h-4 mr-2 text-blue-500" />
                Total Contacts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="total-contacts-count">
                {stats.total_contacts}
              </div>
              <p className="text-sm text-gray-600">People you're tracking</p>
            </CardContent>
          </Card>

          <Card className="stats-card border-0 shadow-lg" data-testid="templates-stat-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <FileText className="w-4 h-4 mr-2 text-green-500" />
                Templates
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="total-templates-count">
                {stats.total_templates}
              </div>
              <p className="text-sm text-gray-600">Message templates</p>
            </CardContent>
          </Card>

          <Card className="stats-card border-0 shadow-lg" data-testid="upcoming-events-stat-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <Calendar className="w-4 h-4 mr-2 text-rose-500" />
                Upcoming Events
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-1" data-testid="upcoming-events-count">
                {stats.upcoming_events.length}
              </div>
              <p className="text-sm text-gray-600">Next 30 days</p>
            </CardContent>
          </Card>

          <Card className="stats-card border-0 shadow-lg" data-testid="subscription-stat-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <TrendingUp className="w-4 h-4 mr-2 text-purple-500" />
                Subscription
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-gray-900 mb-1 capitalize" data-testid="subscription-status">
                {user?.subscription_status || 'Free'}
              </div>
              <p className="text-sm text-gray-600">Current plan</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upcoming Events */}
          <div className="lg:col-span-2">
            <Card className="border-0 shadow-xl glass" data-testid="upcoming-events-card">
              <CardHeader>
                <CardTitle className="flex items-center text-xl">
                  <Clock className="w-5 h-5 mr-2 text-rose-500" />
                  Upcoming Celebrations
                </CardTitle>
                <CardDescription>
                  Events in the next 30 days that you won't want to miss
                </CardDescription>
              </CardHeader>
              <CardContent>
                {stats.upcoming_events.length === 0 ? (
                  <div className="text-center py-12" data-testid="no-upcoming-events">
                    <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No upcoming events</h3>
                    <p className="text-gray-600 mb-4">Add some contacts with birthdays and anniversaries to see them here!</p>
                    <Button asChild className="btn-gradient">
                      <Link to="/contacts" data-testid="add-contacts-button">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Contacts
                      </Link>
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {stats.upcoming_events.map((event, index) => (
                      <div 
                        key={index} 
                        className="flex items-center justify-between p-4 bg-white/50 rounded-lg border border-white/20 card-hover"
                        data-testid={`upcoming-event-${index}`}
                      >
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            {getEventIcon(event.event_type)}
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900" data-testid={`event-contact-name-${index}`}>
                              {event.contact_name}
                            </h4>
                            <p className="text-sm text-gray-600 capitalize" data-testid={`event-type-${index}`}>
                              {event.event_type}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge 
                            variant="outline" 
                            className={`${getEventColor(event.event_type)} font-medium`}
                            data-testid={`event-days-until-${index}`}
                          >
                            {getDaysUntilText(event.days_until)}
                          </Badge>
                          <p className="text-xs text-gray-500 mt-1" data-testid={`event-date-${index}`}>
                            {formatDate(event.date)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <div className="space-y-6">
            <Card className="border-0 shadow-xl glass" data-testid="quick-actions-card">
              <CardHeader>
                <CardTitle className="flex items-center text-xl">
                  <Sparkles className="w-5 h-5 mr-2 text-rose-500" />
                  Quick Actions
                </CardTitle>
                <CardDescription>
                  Get started with common tasks
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button asChild className="w-full justify-start h-12 bg-white/80 text-gray-700 border border-gray-200 hover:bg-white hover:shadow-md" data-testid="add-contact-action">
                  <Link to="/contacts">
                    <Users className="w-4 h-4 mr-3" />
                    Add New Contact
                  </Link>
                </Button>
                
                <Button asChild className="w-full justify-start h-12 bg-white/80 text-gray-700 border border-gray-200 hover:bg-white hover:shadow-md" data-testid="create-template-action">
                  <Link to="/templates">
                    <FileText className="w-4 h-4 mr-3" />
                    Create Template
                  </Link>
                </Button>
                
                <Button className="w-full justify-start h-12 bg-gradient-to-r from-rose-500 to-orange-400 text-white hover:from-rose-600 hover:to-orange-500" data-testid="generate-message-action">
                  <Sparkles className="w-4 h-4 mr-3" />
                  Generate AI Message
                </Button>
              </CardContent>
            </Card>

            {/* Tips Card */}
            <Card className="border-0 shadow-xl glass" data-testid="tips-card">
              <CardHeader>
                <CardTitle className="text-lg">💡 Pro Tips</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
                  <p className="text-blue-800">
                    <strong>AI Messages:</strong> Use our AI to generate personalized messages for each contact!
                  </p>
                </div>
                <div className="p-3 bg-green-50 rounded-lg border border-green-100">
                  <p className="text-green-800">
                    <strong>Templates:</strong> Create reusable templates to save time on common messages.
                  </p>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg border border-purple-100">
                  <p className="text-purple-800">
                    <strong>Automation:</strong> Set up your contacts and let us handle the rest!
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;