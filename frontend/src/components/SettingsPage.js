import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../App';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { 
  Settings, 
  MessageCircle, 
  Mail, 
  Clock, 
  Bell,
  Save,
  TestTube,
  CheckCircle,
  XCircle,
  AlertCircle,
  Phone,
  Key,
  User,
  Globe,
  Send,
  Coins,
  Infinity
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SettingsPage = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState({
    digitalsms_api_key: '',
    whatsapp_sender_number: '',
    email_api_key: '',
    sender_email: '',
    sender_name: '',
    daily_send_time: '09:00',
    timezone: 'UTC',
    execution_report_enabled: true,
    execution_report_email: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingWhatsApp, setTestingWhatsApp] = useState(false);
  const [testingEmail, setTestingEmail] = useState(false);
  const [whatsappTestResult, setWhatsappTestResult] = useState(null);
  const [emailTestResult, setEmailTestResult] = useState(null);
  const [testPhoneNumber, setTestPhoneNumber] = useState('');
  const [sendingTestMessage, setSendingTestMessage] = useState(false);
  const [credits, setCredits] = useState({
    whatsapp_credits: 0,
    email_credits: 0,
    unlimited_whatsapp: false,
    unlimited_email: false
  });
  
  // Profile state
  const [profileData, setProfileData] = useState({
    full_name: '',
    email: '',
    phone_number: ''
  });
  const [editingProfile, setEditingProfile] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [phoneValidationError, setPhoneValidationError] = useState('');

  const timezones = [
    'UTC', 'America/New_York', 'America/Los_Angeles', 'America/Chicago',
    'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Asia/Tokyo',
    'Asia/Shanghai', 'Asia/Kolkata', 'Australia/Sydney', 'Africa/Cairo'
  ];

  useEffect(() => {
    fetchSettings();
    fetchCredits();
    fetchProfile();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings({
        ...response.data,
        execution_report_email: response.data.execution_report_email || user?.email || ''
      });
    } catch (error) {
      console.error('Error fetching settings:', error);
      toast.error('Failed to load settings');
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

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/user/profile`);
      setProfileData({
        full_name: response.data.full_name || '',
        email: response.data.email || '',
        phone_number: response.data.phone_number || ''
      });
    } catch (error) {
      console.error('Error fetching profile:', error);
      toast.error('Failed to load profile data');
    }
  };

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    
    try {
      const response = await axios.put(`${API}/user/profile`, {
        full_name: profileData.full_name.trim(),
        email: profileData.email.trim(),
        phone_number: profileData.phone_number.trim() || null
      });
      
      toast.success('Profile updated successfully!');
      setEditingProfile(false);
      
      // Update the user context if possible
      // Note: This depends on your auth context implementation
      // You might need to refresh the page or update the auth context
      
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleCancelProfileEdit = () => {
    // Reset profile data to original values
    fetchProfile();
    setEditingProfile(false);
    setPhoneValidationError('');
  };

  const cleanPhoneNumber = (phone) => {
    if (!phone) return '';
    
    // Remove all spaces, dashes, parentheses
    let cleaned = phone.replace(/[\s\-\(\)]/g, '');
    
    // Remove +91 country code if present
    if (cleaned.startsWith('+91')) {
      cleaned = cleaned.substring(3);
    } else if (cleaned.startsWith('91') && cleaned.length === 12) {
      cleaned = cleaned.substring(2);
    }
    
    // Keep only digits
    cleaned = cleaned.replace(/\D/g, '');
    
    // Limit to 10 digits for Indian numbers
    if (cleaned.length > 10) {
      cleaned = cleaned.substring(0, 10);
    }
    
    return cleaned;
  };

  const handlePhoneNumberChange = (e) => {
    const rawValue = e.target.value;
    const cleanedValue = cleanPhoneNumber(rawValue);
    
    // Validate the cleaned value
    let validationError = '';
    if (cleanedValue && cleanedValue.length > 0) {
      if (cleanedValue.length !== 10) {
        validationError = 'Phone number must be exactly 10 digits';
      } else if (!/^[6-9]/.test(cleanedValue)) {
        validationError = 'Phone number must start with 6, 7, 8, or 9';
      }
    }
    
    setPhoneValidationError(validationError);
    setProfileData({ ...profileData, phone_number: cleanedValue });
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    
    try {
      const response = await axios.put(`${API}/settings`, settings);
      setSettings(response.data);
      toast.success('Settings saved successfully!');
      
      // Clear test results after saving
      setWhatsappTestResult(null);
      setEmailTestResult(null);
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const testWhatsAppConfig = async () => {
    const isConfigComplete = settings.whatsapp_provider === 'facebook' 
      ? (settings.whatsapp_phone_number_id && settings.whatsapp_access_token)
      : (settings.whatsapp_provider === 'digitalsms' && settings.digitalsms_api_key);

    if (!isConfigComplete) {
      toast.error('Please configure WhatsApp settings first');
      return;
    }

    setTestingWhatsApp(true);
    setWhatsappTestResult(null);

    try {
      const response = await axios.post(`${API}/settings/test-whatsapp`);
      setWhatsappTestResult(response.data);
      
      if (response.data.status === 'success') {
        toast.success('WhatsApp configuration test successful!');
      } else {
        toast.error('WhatsApp configuration test failed');
      }
    } catch (error) {
      console.error('Error testing WhatsApp config:', error);
      setWhatsappTestResult({
        status: 'error',
        message: error.response?.data?.detail || 'Test failed'
      });
      toast.error('WhatsApp configuration test failed');
    } finally {
      setTestingWhatsApp(false);
    }
  };

  const sendTestWhatsAppMessage = async () => {
    if (!testPhoneNumber.trim()) {
      toast.error('Please enter a phone number for testing');
      return;
    }

    setSendingTestMessage(true);

    try {
      const response = await axios.post(`${API}/send-whatsapp-test`, null, {
        params: { phone_number: testPhoneNumber }
      });

      if (response.data.status === 'success') {
        toast.success('Test WhatsApp message sent successfully!');
      } else {
        toast.error(`Failed to send test message: ${response.data.message}`);
      }
    } catch (error) {
      console.error('Error sending test message:', error);
      toast.error(error.response?.data?.detail || 'Failed to send test message');
    } finally {
      setSendingTestMessage(false);
    }
  };

  const testEmailConfig = async () => {
    if (!settings.email_api_key || !settings.sender_email) {
      toast.error('Please configure email settings first');
      return;
    }

    setTestingEmail(true);
    setEmailTestResult(null);

    try {
      const response = await axios.post(`${API}/settings/test-email`);
      setEmailTestResult(response.data);
      
      if (response.data.status === 'success') {
        toast.success('Email configuration test successful! Check your inbox.');
      } else {
        toast.error('Email configuration test failed');
      }
    } catch (error) {
      console.error('Error testing email config:', error);
      setEmailTestResult({
        status: 'error',
        message: error.response?.data?.detail || 'Test failed'
      });
      toast.error('Email configuration test failed');
    } finally {
      setTestingEmail(false);
    }
  };

  const formatTime = (time) => {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" data-testid="settings-page">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center" data-testid="settings-title">
            <Settings className="w-8 h-8 mr-3 text-rose-500" />
            Account Settings
          </h1>
          <p className="text-gray-600">
            Configure your API settings, scheduling preferences, and notifications
          </p>
        </div>

        {/* Credits Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Card className="border-0 shadow-lg bg-gradient-to-r from-green-50 to-emerald-50">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-medium text-gray-700 flex items-center">
                <MessageCircle className="w-5 h-5 mr-2 text-green-500" />
                WhatsApp Credits
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900 flex items-center">
                {credits.unlimited_whatsapp ? (
                  <>
                    <Infinity className="w-6 h-6 text-green-600 mr-2" />
                    <span className="text-green-600">Unlimited</span>
                  </>
                ) : (
                  <>
                    {credits.whatsapp_credits}
                    <Coins className="w-5 h-5 text-green-600 ml-2" />
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg bg-gradient-to-r from-blue-50 to-cyan-50">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-medium text-gray-700 flex items-center">
                <Mail className="w-5 h-5 mr-2 text-blue-500" />
                Email Credits
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900 flex items-center">
                {credits.unlimited_email ? (
                  <>
                    <Infinity className="w-6 h-6 text-blue-600 mr-2" />
                    <span className="text-blue-600">Unlimited</span>
                  </>
                ) : (
                  <>
                    {credits.email_credits}
                    <Coins className="w-5 h-5 text-blue-600 ml-2" />
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="apis" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="apis">API Configuration</TabsTrigger>
            <TabsTrigger value="scheduling">Scheduling</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="account">Account</TabsTrigger>
          </TabsList>

          {/* API Configuration Tab */}
          <TabsContent value="apis" className="space-y-6">
            {/* WhatsApp API Configuration */}
            <Card className="border-0 shadow-xl glass">
              <CardHeader>
                <CardTitle className="flex items-center text-xl">
                  <MessageCircle className="w-5 h-5 mr-2 text-green-500" />
                  WhatsApp API Configuration
                </CardTitle>
                <CardDescription>
                  Configure WhatsApp messaging using DigitalSMS API
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* DigitalSMS API Configuration */}
                <div className="space-y-4 p-4 bg-green-50 rounded-lg border border-green-200">
                  <h4 className="font-medium text-green-900 flex items-center">
                    <MessageCircle className="w-4 h-4 mr-2" />
                    DigitalSMS API Configuration
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="digitalsms-api-key" className="flex items-center">
                        <Key className="w-4 h-4 mr-2" />
                        API Key *
                      </Label>
                      <Input
                        id="digitalsms-api-key"
                        data-testid="digitalsms-api-key-input"
                        type="password"
                        value={settings.digitalsms_api_key}
                        onChange={(e) => setSettings({ ...settings, digitalsms_api_key: e.target.value })}
                        placeholder="Enter DigitalSMS API Key"
                        required
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="whatsapp-sender-number" className="flex items-center">
                        <Phone className="w-4 h-4 mr-2" />
                        Sender Phone Number *
                      </Label>
                      <Input
                        id="whatsapp-sender-number"
                        data-testid="whatsapp-sender-number-input"
                        type="tel"
                        value={settings.whatsapp_sender_number}
                        onChange={(e) => {
                          // Clean and validate 10-digit Indian mobile number
                          const cleaned = e.target.value.replace(/[^\d]/g, '').substring(0, 10);
                          setSettings({ ...settings, whatsapp_sender_number: cleaned });
                        }}
                        placeholder="Enter 10-digit sender number"
                        maxLength={10}
                        required
                      />
                      <p className="text-xs text-gray-500">
                        10-digit Indian mobile number for sending WhatsApp messages
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-xs text-green-700 bg-green-100 p-3 rounded-lg">
                    <strong>DigitalSMS API Details:</strong><br/>
                    <strong>Endpoint:</strong> https://demo.digitalsms.biz/api<br/>
                    <strong>Required Parameters:</strong> apikey, mobile, msg<br/>
                    <strong>Optional Parameters:</strong> img1 (image URL), pdf (PDF URL), video (video URL)<br/>
                    <strong>Example:</strong> ?apikey=yourkey&mobile=9876543210&msg=Happy Birthday!&img1=https://example.com/image.jpg
                  </div>
                  
                  <Alert className="border-blue-200 bg-blue-50">
                    <AlertCircle className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="text-blue-800">
                      <strong>Features:</strong> Supports text messages with image, PDF, and video attachments. 
                      Media files must be accessible via live URLs (max 1MB for images, 3MB for PDF/videos).
                    </AlertDescription>
                  </Alert>
                </div>

                <div className="space-y-4 pt-4 border-t">
                  {/* Configuration Test */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Button
                        onClick={testWhatsAppConfig}
                        disabled={testingWhatsApp || !settings.digitalsms_api_key}
                        variant="outline"
                        size="sm"
                        data-testid="test-whatsapp-button"
                      >
                        {testingWhatsApp ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b border-gray-600 mr-2" />
                        ) : (
                          <TestTube className="w-4 h-4 mr-2" />
                        )}
                        Test Configuration
                      </Button>

                      {whatsappTestResult && (
                        <Badge
                          variant="outline"
                          className={whatsappTestResult.status === 'success' 
                            ? 'bg-green-100 text-green-700 border-green-200'
                            : 'bg-red-100 text-red-700 border-red-200'
                          }
                        >
                          {whatsappTestResult.status === 'success' ? (
                            <CheckCircle className="w-3 h-3 mr-1" />
                          ) : (
                            <XCircle className="w-3 h-3 mr-1" />
                          )}
                          {whatsappTestResult.status === 'success' ? 'Valid' : 'Invalid'}
                        </Badge>
                      )}
                    </div>

                    <div className="text-xs text-gray-500">
                      Provider: DigitalSMS API
                    </div>
                  </div>

                  {/* Real Message Test */}
                  {whatsappTestResult?.status === 'success' && (
                    <div className="space-y-2 p-3 bg-green-50 rounded-lg border border-green-200">
                      <Label className="text-sm font-medium text-green-800">Send Test Message</Label>
                      <div className="flex space-x-2">
                        <Input
                          placeholder="Enter phone number (e.g., +1234567890)"
                          value={testPhoneNumber}
                          onChange={(e) => setTestPhoneNumber(e.target.value)}
                          className="flex-1"
                          data-testid="test-phone-input"
                        />
                        <Button
                          onClick={sendTestWhatsAppMessage}
                          disabled={sendingTestMessage || !testPhoneNumber.trim()}
                          size="sm"
                          className="bg-green-600 hover:bg-green-700 text-white"
                          data-testid="send-test-message-button"
                        >
                          {sendingTestMessage ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b border-white mr-2" />
                          ) : (
                            <Send className="w-4 h-4 mr-2" />
                          )}
                          Send Test
                        </Button>
                      </div>
                      <p className="text-xs text-green-700">
                        This will send an actual WhatsApp message to verify your {settings.whatsapp_provider === 'facebook' ? 'Facebook' : 'DigitalSMS'} API configuration.
                      </p>
                    </div>
                  )}
                </div>

                {whatsappTestResult?.status === 'error' && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-800">
                      {whatsappTestResult.message}
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* Email API Configuration */}
            <Card className="border-0 shadow-xl glass">
              <CardHeader>
                <CardTitle className="flex items-center text-xl">
                  <Mail className="w-5 h-5 mr-2 text-blue-500" />
                  Email API Configuration
                </CardTitle>
                <CardDescription>
                  Configure Brevo (SendinBlue) API for email delivery
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="email-api-key" className="flex items-center">
                      <Key className="w-4 h-4 mr-2" />
                      Brevo API Key
                    </Label>
                    <Input
                      id="email-api-key"
                      data-testid="email-api-key-input"
                      type="password"
                      value={settings.email_api_key}
                      onChange={(e) => setSettings({ ...settings, email_api_key: e.target.value })}
                      placeholder="Enter Brevo API Key"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="sender-email" className="flex items-center">
                      <Mail className="w-4 h-4 mr-2" />
                      Sender Email
                    </Label>
                    <Input
                      id="sender-email"
                      data-testid="sender-email-input"
                      type="email"
                      value={settings.sender_email}
                      onChange={(e) => setSettings({ ...settings, sender_email: e.target.value })}
                      placeholder="sender@yourdomain.com"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sender-name" className="flex items-center">
                    <User className="w-4 h-4 mr-2" />
                    Sender Name
                  </Label>
                  <Input
                    id="sender-name"
                    data-testid="sender-name-input"
                    value={settings.sender_name}
                    onChange={(e) => setSettings({ ...settings, sender_name: e.target.value })}
                    placeholder="ReminderAI"
                  />
                </div>

                <div className="flex items-center justify-between pt-4 border-t">
                  <div className="flex items-center space-x-3">
                    <Button
                      onClick={testEmailConfig}
                      disabled={testingEmail || !settings.email_api_key || !settings.sender_email}
                      variant="outline"
                      size="sm"
                      data-testid="test-email-button"
                    >
                      {testingEmail ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b border-gray-600 mr-2" />
                      ) : (
                        <TestTube className="w-4 h-4 mr-2" />
                      )}
                      Test Configuration
                    </Button>

                    {emailTestResult && (
                      <Badge
                        variant="outline"
                        className={emailTestResult.status === 'success' 
                          ? 'bg-green-100 text-green-700 border-green-200'
                          : 'bg-red-100 text-red-700 border-red-200'
                        }
                      >
                        {emailTestResult.status === 'success' ? (
                          <CheckCircle className="w-3 h-3 mr-1" />
                        ) : (
                          <XCircle className="w-3 h-3 mr-1" />
                        )}
                        {emailTestResult.status === 'success' ? 'Valid' : 'Invalid'}
                      </Badge>
                    )}
                  </div>

                  <div className="text-xs text-gray-500">
                    Endpoint: https://api.brevo.com/v3/smtp/email
                  </div>
                </div>

                {emailTestResult?.status === 'error' && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-800">
                      {emailTestResult.message}
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Scheduling Tab */}
          <TabsContent value="scheduling" className="space-y-6">
            <Card className="border-0 shadow-xl glass">
              <CardHeader>
                <CardTitle className="flex items-center text-xl">
                  <Clock className="w-5 h-5 mr-2 text-purple-500" />
                  Daily Scheduling
                </CardTitle>
                <CardDescription>
                  Configure when birthday and anniversary messages are sent daily
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="daily-time" className="flex items-center">
                      <Clock className="w-4 h-4 mr-2" />
                      Daily Send Time
                    </Label>
                    <Input
                      id="daily-time"
                      data-testid="daily-time-input"
                      type="time"
                      value={settings.daily_send_time}
                      onChange={(e) => setSettings({ ...settings, daily_send_time: e.target.value })}
                    />
                    <p className="text-sm text-gray-500">
                      Messages will be sent at {formatTime(settings.daily_send_time)} in your selected timezone
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="timezone" className="flex items-center">
                      <Globe className="w-4 h-4 mr-2" />
                      Timezone
                    </Label>
                    <Select 
                      value={settings.timezone} 
                      onValueChange={(value) => setSettings({ ...settings, timezone: value })}
                    >
                      <SelectTrigger data-testid="timezone-select">
                        <SelectValue placeholder="Select timezone" />
                      </SelectTrigger>
                      <SelectContent>
                        {timezones.map((tz) => (
                          <SelectItem key={tz} value={tz}>
                            {tz}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Alert>
                  <Clock className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Automatic Scheduling:</strong> Messages will be automatically sent every day at your specified time for contacts who have birthdays or anniversaries that day.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications" className="space-y-6">
            <Card className="border-0 shadow-xl glass">
              <CardHeader>
                <CardTitle className="flex items-center text-xl">
                  <Bell className="w-5 h-5 mr-2 text-orange-500" />
                  Execution Reports
                </CardTitle>
                <CardDescription>
                  Configure execution reports sent after daily message processing
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label className="text-base">Enable Execution Reports</Label>
                    <p className="text-sm text-gray-500">
                      Receive a summary email after each daily message execution
                    </p>
                  </div>
                  <Switch
                    checked={settings.execution_report_enabled}
                    onCheckedChange={(checked) => setSettings({ ...settings, execution_report_enabled: checked })}
                    data-testid="execution-report-switch"
                  />
                </div>

                {settings.execution_report_enabled && (
                  <div className="space-y-2">
                    <Label htmlFor="report-email" className="flex items-center">
                      <Mail className="w-4 h-4 mr-2" />
                      Report Email Address
                    </Label>
                    <Input
                      id="report-email"
                      data-testid="report-email-input"
                      type="email"
                      value={settings.execution_report_email}
                      onChange={(e) => setSettings({ ...settings, execution_report_email: e.target.value })}
                      placeholder="Enter email for execution reports"
                    />
                    <p className="text-sm text-gray-500">
                      Reports will include recipient names, contact details, and message status
                    </p>
                  </div>
                )}

                <Alert>
                  <Send className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Report Contents:</strong> Each execution report will include:
                    <ul className="mt-2 space-y-1 text-sm">
                      <li>• Recipient names and contact information</li>
                      <li>• Messages sent successfully</li>
                      <li>• Failed deliveries with error details</li>
                      <li>• Summary statistics</li>
                    </ul>
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Account Tab */}
          <TabsContent value="account" className="space-y-6">
            <Card className="border-0 shadow-xl glass">
              <CardHeader>
                <CardTitle className="flex items-center text-xl justify-between">
                  <div className="flex items-center">
                    <User className="w-5 h-5 mr-2 text-gray-500" />
                    Account Information
                  </div>
                  {!editingProfile && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setEditingProfile(true)}
                      className="text-sm"
                      data-testid="edit-profile-button"
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      Edit Profile
                    </Button>
                  )}
                </CardTitle>
                <CardDescription>
                  {editingProfile ? 'Update your personal information' : 'Your account details and subscription status'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {editingProfile ? (
                  /* Editable Profile Form */
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="profile-name" className="flex items-center">
                          <User className="w-4 h-4 mr-2" />
                          Full Name *
                        </Label>
                        <Input
                          id="profile-name"
                          data-testid="profile-name-input"
                          value={profileData.full_name}
                          onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                          placeholder="Enter your full name"
                          required
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="profile-email" className="flex items-center">
                          <Mail className="w-4 h-4 mr-2" />
                          Email Address *
                        </Label>
                        <Input
                          id="profile-email"
                          data-testid="profile-email-input"
                          type="email"
                          value={profileData.email}
                          onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                          placeholder="Enter your email address"
                          required
                        />
                      </div>
                      
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor="profile-phone" className="flex items-center">
                          <Phone className="w-4 h-4 mr-2" />
                          Phone Number (Optional)
                        </Label>
                        <Input
                          id="profile-phone"
                          data-testid="profile-phone-input"
                          type="tel"
                          value={profileData.phone_number}
                          onChange={handlePhoneNumberChange}
                          placeholder="Enter 10-digit mobile number (e.g., 9876543210)"
                          maxLength={10}
                          className={phoneValidationError ? 'border-red-300 focus:border-red-500' : ''}
                        />
                        {phoneValidationError && (
                          <p className="text-xs text-red-600 flex items-center">
                            <XCircle className="w-3 h-3 mr-1" />
                            {phoneValidationError}
                          </p>
                        )}
                        <p className="text-xs text-gray-500">
                          Indian mobile numbers only. Must be 10 digits starting with 6, 7, 8, or 9. +91 will be automatically removed.
                        </p>
                      </div>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="flex justify-end space-x-3 pt-4 border-t">
                      <Button
                        variant="outline"
                        onClick={handleCancelProfileEdit}
                        disabled={savingProfile}
                        data-testid="cancel-profile-button"
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleSaveProfile}
                        disabled={savingProfile || !profileData.full_name.trim() || !profileData.email.trim() || phoneValidationError}
                        className="btn-gradient"
                        data-testid="save-profile-button"
                      >
                        {savingProfile ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b border-white mr-2" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="w-4 h-4 mr-2" />
                            Save Changes
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                ) : (
                  /* Read-only Profile Display */
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm text-gray-600">Full Name</Label>
                      <p className="font-medium" data-testid="display-name">
                        {profileData.full_name || user?.full_name || 'Not set'}
                      </p>
                    </div>
                    <div>
                      <Label className="text-sm text-gray-600">Email Address</Label>
                      <p className="font-medium" data-testid="display-email">
                        {profileData.email || user?.email || 'Not set'}
                      </p>
                    </div>
                    <div>
                      <Label className="text-sm text-gray-600">Phone Number</Label>
                      <p className="font-medium" data-testid="display-phone">
                        {profileData.phone_number || 'Not set'}
                      </p>
                    </div>
                    <div>
                      <Label className="text-sm text-gray-600">Subscription Status</Label>
                      <Badge 
                        variant="outline" 
                        className={`${
                          user?.subscription_status === 'active' 
                            ? 'bg-green-100 text-green-700 border-green-200'
                            : user?.subscription_status === 'trial'
                            ? 'bg-blue-100 text-blue-700 border-blue-200'
                            : 'bg-gray-100 text-gray-700 border-gray-200'
                        } capitalize`}
                        data-testid="subscription-status"
                      >
                        {user?.subscription_status || 'Trial'}
                      </Badge>
                    </div>
                    <div className="md:col-span-2">
                      <Label className="text-sm text-gray-600">Member Since</Label>
                      <p className="font-medium" data-testid="member-since">
                        {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        }) : 'N/A'}
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Save Button */}
        <div className="flex justify-end mt-8">
          <Button
            onClick={handleSaveSettings}
            disabled={saving}
            className="btn-gradient px-8"
            data-testid="save-settings-button"
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b border-white mr-2" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save All Settings
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;