import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Switch } from './ui/switch';
import { toast } from 'sonner';
import { 
  Plus, 
  Edit, 
  Trash2, 
  FileText, 
  Mail, 
  MessageCircle,
  Search,
  Star,
  Copy,
  Sparkles,
  Image,
  XCircle
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TemplatesPage = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [formData, setFormData] = useState({
    name: '',
    type: 'email',
    subject: '',
    content: '',
    is_default: false,
    whatsapp_image_url: '',
    email_image_url: ''
  });
  const [uploadingImage, setUploadingImage] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
      toast.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const templateData = {
        ...formData,
        subject: formData.type === 'email' ? formData.subject : null
      };

      if (editingTemplate) {
        await axios.put(`${API}/templates/${editingTemplate.id}`, templateData);
        toast.success('Template updated successfully!');
      } else {
        await axios.post(`${API}/templates`, templateData);
        toast.success('Template created successfully!');
      }
      
      resetForm();
      setIsDialogOpen(false);
      fetchTemplates();
    } catch (error) {
      console.error('Error saving template:', error);
      toast.error(error.response?.data?.detail || 'Failed to save template');
    }
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name || '',
      type: template.type || 'email',
      subject: template.subject || '',
      content: template.content || '',
      is_default: template.is_default || false,
      whatsapp_image_url: template.whatsapp_image_url || '',
      email_image_url: template.email_image_url || ''
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (templateId, templateName) => {
    if (window.confirm(`Are you sure you want to delete "${templateName}"?`)) {
      try {
        await axios.delete(`${API}/templates/${templateId}`);
        toast.success('Template deleted successfully!');
        fetchTemplates();
      } catch (error) {
        console.error('Error deleting template:', error);
        toast.error('Failed to delete template');
      }
    }
  };

  const copyToClipboard = (content) => {
    navigator.clipboard.writeText(content);
    toast.success('Template content copied to clipboard!');
  };

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'email',
      subject: '',
      content: '',
      is_default: false,
      whatsapp_image_url: '',
      email_image_url: ''
    });
    setEditingTemplate(null);
  };

  const handleImageUpload = async (event, imageType) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingImage(true);
    try {
      const formDataUpload = new FormData();
      formDataUpload.append('file', file);

      const response = await axios.post(`${API}/upload-image`, formDataUpload, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const imageUrl = response.data.image_url;
      setFormData(prev => ({
        ...prev,
        [imageType]: imageUrl
      }));
      
      toast.success('Image uploaded successfully');
    } catch (error) {
      console.error('Error uploading image:', error);
      toast.error('Failed to upload image');
    } finally {
      setUploadingImage(false);
    }
  };

  const getTemplateIcon = (type) => {
    return type === 'email' ? (
      <Mail className="w-4 h-4 text-blue-500" />
    ) : (
      <MessageCircle className="w-4 h-4 text-green-500" />
    );
  };

  const getTemplateColor = (type, isDefault = false) => {
    if (isDefault) {
      return 'bg-yellow-100 text-yellow-700 border-yellow-200';
    }
    return type === 'email' 
      ? 'bg-blue-100 text-blue-700 border-blue-200'
      : 'bg-green-100 text-green-700 border-green-200';
  };

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.content.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || template.type === filterType;
    return matchesSearch && matchesType;
  });

  const defaultTemplates = [
    {
      type: 'email',
      name: 'Birthday Celebration',
      subject: 'Happy Birthday, {name}! 🎉',
      content: 'Dear {name},\n\nWishing you a very happy birthday! May this special day bring you joy, laughter, and all the wonderful things you deserve. Here\'s to another year of amazing adventures and beautiful memories.\n\nHave a fantastic celebration!\n\nBest wishes,\n{your_name}'
    },
    {
      type: 'whatsapp',
      name: 'Anniversary Wishes',
      subject: '',
      content: '🎊 Happy Anniversary {name}! 💕\n\nCelebrating another year of love, laughter, and beautiful memories together. Wishing you both continued happiness and many more wonderful years ahead!\n\n#Anniversary #Love #Celebration'
    },
    {
      type: 'email',
      name: 'Professional Birthday',
      subject: 'Birthday Wishes - {name}',
      content: 'Dear {name},\n\nOn behalf of the entire team, I would like to wish you a very happy birthday! We hope you have a wonderful day filled with celebration and joy.\n\nThank you for being such a valuable part of our community.\n\nWarm regards,\n{your_name}'
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-rose-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6" data-testid="templates-page">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2" data-testid="templates-title">
              Message Templates
            </h1>
            <p className="text-gray-600">
              Create and manage reusable message templates for your celebrations
            </p>
          </div>
          
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button 
                className="btn-gradient" 
                onClick={resetForm}
                data-testid="add-template-button"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Template
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-2xl">
              <DialogHeader>
                <DialogTitle data-testid="template-dialog-title">
                  {editingTemplate ? 'Edit Template' : 'Create New Template'}
                </DialogTitle>
                <DialogDescription>
                  {editingTemplate 
                    ? 'Update your message template below.'
                    : 'Create a reusable message template for birthdays or anniversaries.'
                  }
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="template-name">Template Name *</Label>
                    <Input
                      id="template-name"
                      data-testid="template-name-input"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g., Birthday Celebration"
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="template-type">Type *</Label>
                    <Select 
                      value={formData.type} 
                      onValueChange={(value) => {
                        // Clear irrelevant image when type changes
                        const updatedFormData = { ...formData, type: value };
                        if (value === 'whatsapp') {
                          updatedFormData.email_image_url = ''; // Clear email image for WhatsApp template
                        } else if (value === 'email') {
                          updatedFormData.whatsapp_image_url = ''; // Clear WhatsApp image for Email template
                        }
                        setFormData(updatedFormData);
                      }}
                    >
                      <SelectTrigger data-testid="template-type-select">
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="email">Email</SelectItem>
                        <SelectItem value="whatsapp">WhatsApp</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                {formData.type === 'email' && (
                  <div className="space-y-2">
                    <Label htmlFor="template-subject">Email Subject</Label>
                    <Input
                      id="template-subject"
                      data-testid="template-subject-input"
                      value={formData.subject}
                      onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                      placeholder="e.g., Happy Birthday, {name}! 🎉"
                    />
                  </div>
                )}
                
                <div className="space-y-2">
                  <Label htmlFor="template-content">Message Content *</Label>
                  <Textarea
                    id="template-content"
                    data-testid="template-content-input"
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    placeholder="Write your message template here...\n\nTip: Use {name} to insert the contact's name"
                    className="min-h-[150px] resize-y"
                    required
                  />
                </div>
                
                {/* Image Upload Section - Only show relevant image based on template type */}
                <div className="space-y-4 p-4 bg-gray-50 rounded-lg border">
                  <h4 className="text-sm font-medium text-gray-700 flex items-center">
                    <Image className="w-4 h-4 mr-2" />
                    Default Image (Optional)
                  </h4>
                  <p className="text-xs text-gray-500">
                    This image will be used by default if no custom image is set for individual contacts
                  </p>
                  
                  {/* WhatsApp Image Upload - Only for WhatsApp templates */}
                  {formData.type === 'whatsapp' && (
                    <div className="space-y-2">
                      <Label htmlFor="whatsapp-image-upload" className="text-sm flex items-center">
                        <MessageCircle className="w-4 h-4 mr-2 text-green-600" />
                        WhatsApp Default Image
                      </Label>
                      <div className="flex items-center space-x-2">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleImageUpload(e, 'whatsapp_image_url')}
                          className="hidden"
                          id="whatsapp-image-upload"
                          disabled={uploadingImage}
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => document.getElementById('whatsapp-image-upload').click()}
                          disabled={uploadingImage}
                          className="text-xs"
                        >
                          {uploadingImage ? (
                            <>
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600 mr-1"></div>
                              Uploading...
                            </>
                          ) : (
                            <>
                              <Image className="w-3 h-3 mr-1" />
                              {formData.whatsapp_image_url ? 'Change' : 'Upload'}
                            </>
                          )}
                        </Button>
                        
                        {formData.whatsapp_image_url && (
                          <div className="flex items-center space-x-2">
                            <img 
                              src={formData.whatsapp_image_url.startsWith('http') 
                                ? formData.whatsapp_image_url 
                                : `${BACKEND_URL}${formData.whatsapp_image_url}`} 
                              alt="WhatsApp default" 
                              className="w-8 h-8 rounded object-cover border"
                              onError={(e) => {
                                console.error('WhatsApp image failed to load:', formData.whatsapp_image_url);
                                console.error('Constructed URL:', e.target.src);
                              }}
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => setFormData(prev => ({ ...prev, whatsapp_image_url: '' }))}
                              className="text-red-500 hover:text-red-700 h-6 w-6 p-0"
                            >
                              <XCircle className="w-3 h-3" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Email Image Upload - Only for Email templates */}
                  {formData.type === 'email' && (
                    <div className="space-y-2">
                      <Label htmlFor="email-image-upload" className="text-sm flex items-center">
                        <Mail className="w-4 h-4 mr-2 text-blue-600" />
                        Email Default Image
                      </Label>
                      <div className="flex items-center space-x-2">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleImageUpload(e, 'email_image_url')}
                          className="hidden"
                          id="email-image-upload"
                          disabled={uploadingImage}
                        />
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => document.getElementById('email-image-upload').click()}
                          disabled={uploadingImage}
                          className="text-xs"
                        >
                          {uploadingImage ? (
                            <>
                              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600 mr-1"></div>
                              Uploading...
                            </>
                          ) : (
                            <>
                              <Image className="w-3 h-3 mr-1" />
                              {formData.email_image_url ? 'Change' : 'Upload'}
                            </>
                          )}
                        </Button>
                        
                        {formData.email_image_url && (
                          <div className="flex items-center space-x-2">
                            <img 
                              src={`${BACKEND_URL}${formData.email_image_url}`} 
                              alt="Email default" 
                              className="w-8 h-8 rounded object-cover border"
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => setFormData(prev => ({ ...prev, email_image_url: '' }))}
                              className="text-red-500 hover:text-red-700 h-6 w-6 p-0"
                            >
                              <XCircle className="w-3 h-3" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    id="is-default"
                    data-testid="template-default-switch"
                    checked={formData.is_default}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_default: checked })}
                  />
                  <Label htmlFor="is-default" className="text-sm font-medium">
                    Set as default template for {formData.type === 'email' ? 'emails' : 'WhatsApp messages'}
                  </Label>
                </div>
                
                <div className="flex justify-end space-x-2 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsDialogOpen(false)}
                    data-testid="cancel-template-button"
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit" 
                    className="btn-gradient"
                    data-testid="save-template-button"
                  >
                    {editingTemplate ? 'Update Template' : 'Create Template'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Search and Filter */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              data-testid="templates-search-input"
              placeholder="Search templates..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-white/50"
            />
          </div>
          
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-full sm:w-[180px] bg-white/50" data-testid="templates-filter-select">
              <SelectValue placeholder="Filter by type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="email">Email Templates</SelectItem>
              <SelectItem value="whatsapp">WhatsApp Templates</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Templates Grid */}
        {filteredTemplates.length === 0 && templates.length === 0 ? (
          <div className="text-center py-16" data-testid="no-templates-message">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No templates yet
            </h3>
            <p className="text-gray-600 mb-6">
              Create your first message template to get started!
            </p>
            
            {/* Default Templates */}
            <div className="mb-8">
              <h4 className="text-md font-medium text-gray-700 mb-4">Or try these starter templates:</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
                {defaultTemplates.map((template, index) => (
                  <Card key={index} className="text-left glass border-0 shadow-md">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center">
                        {getTemplateIcon(template.type)}
                        <span className="ml-2">{template.name}</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-xs text-gray-600 mb-3 line-clamp-3">
                        {template.content.substring(0, 100)}...
                      </p>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setFormData({
                            name: template.name,
                            type: template.type,
                            subject: template.subject,
                            content: template.content,
                            is_default: false
                          });
                          setIsDialogOpen(true);
                        }}
                        className="w-full text-xs"
                        data-testid={`use-default-template-${index}`}
                      >
                        <Sparkles className="w-3 h-3 mr-1" />
                        Use This Template
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
            
            <Button 
              className="btn-gradient" 
              onClick={() => {
                resetForm();
                setIsDialogOpen(true);
              }}
              data-testid="create-first-template-button"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Template
            </Button>
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-16" data-testid="no-filtered-templates-message">
            <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No templates found
            </h3>
            <p className="text-gray-600">
              Try adjusting your search terms or filters
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6" data-testid="templates-grid">
            {filteredTemplates.map((template) => (
              <Card 
                key={template.id} 
                className="card-hover glass border-0 shadow-lg"
                data-testid={`template-card-${template.id}`}
              >
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-lg font-semibold text-gray-900 mb-2 flex items-center" data-testid={`template-name-${template.id}`}>
                        {getTemplateIcon(template.type)}
                        <span className="ml-2">{template.name}</span>
                        {template.is_default && (
                          <Star className="w-4 h-4 ml-2 text-yellow-500 fill-current" />
                        )}
                      </CardTitle>
                      
                      <div className="flex flex-wrap gap-2">
                        <Badge 
                          variant="outline" 
                          className={getTemplateColor(template.type, template.is_default)}
                          data-testid={`template-type-${template.id}`}
                        >
                          {template.type.toUpperCase()}
                          {template.is_default && ' • DEFAULT'}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="flex space-x-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => copyToClipboard(template.content)}
                        className="h-8 w-8 p-0 hover:bg-green-50 hover:text-green-600"
                        data-testid={`copy-template-${template.id}`}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleEdit(template)}
                        className="h-8 w-8 p-0 hover:bg-blue-50 hover:text-blue-600"
                        data-testid={`edit-template-${template.id}`}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(template.id, template.name)}
                        className="h-8 w-8 p-0 hover:bg-red-50 hover:text-red-600"
                        data-testid={`delete-template-${template.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-3">
                  {template.subject && template.type === 'email' && (
                    <div data-testid={`template-subject-${template.id}`}>
                      <p className="text-sm font-medium text-gray-700 mb-1">Subject:</p>
                      <p className="text-sm text-gray-600 bg-gray-50 rounded px-3 py-2">
                        {template.subject}
                      </p>
                    </div>
                  )}
                  
                  <div data-testid={`template-content-${template.id}`}>
                    <p className="text-sm font-medium text-gray-700 mb-1">Content:</p>
                    <div className="text-sm text-gray-600 bg-gray-50 rounded px-3 py-2 max-h-32 overflow-y-auto">
                      <pre className="whitespace-pre-wrap font-sans">{template.content}</pre>
                    </div>
                  </div>
                  
                  {/* Image Indicator - Only show relevant image based on template type */}
                  {((template.type === 'whatsapp' && template.whatsapp_image_url) || 
                    (template.type === 'email' && template.email_image_url)) && (
                    <div className="flex items-center space-x-2 pt-2">
                      <p className="text-xs font-medium text-gray-600">Default Image:</p>
                      
                      {/* WhatsApp Image - Only show for WhatsApp templates */}
                      {template.type === 'whatsapp' && template.whatsapp_image_url && (
                        <div className="flex items-center space-x-2 bg-green-50 px-2 py-1 rounded-lg border border-green-200">
                          <MessageCircle className="w-3 h-3 text-green-600" />
                          <span className="text-xs text-green-600 font-medium">WhatsApp</span>
                          <img 
                            src={`${BACKEND_URL}${template.whatsapp_image_url}`} 
                            alt="WhatsApp default" 
                            className="w-8 h-8 rounded object-cover border border-green-300"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              console.log('WhatsApp image failed to load:', template.whatsapp_image_url);
                            }}
                          />
                        </div>
                      )}
                      
                      {/* Email Image - Only show for Email templates */}
                      {template.type === 'email' && template.email_image_url && (
                        <div className="flex items-center space-x-2 bg-blue-50 px-2 py-1 rounded-lg border border-blue-200">
                          <Mail className="w-3 h-3 text-blue-600" />
                          <span className="text-xs text-blue-600 font-medium">Email</span>
                          <img 
                            src={`${BACKEND_URL}${template.email_image_url}`} 
                            alt="Email default" 
                            className="w-8 h-8 rounded object-cover border border-blue-300"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              console.log('Email image failed to load:', template.email_image_url);
                            }}
                          />
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div className="text-xs text-gray-500 pt-2 border-t border-gray-100">
                    Created: {new Date(template.created_at).toLocaleDateString()}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
        
        {/* Stats Footer */}
        {filteredTemplates.length > 0 && (
          <div className="mt-8 text-center" data-testid="templates-stats">
            <p className="text-gray-600">
              Showing {filteredTemplates.length} of {templates.length} templates
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TemplatesPage;