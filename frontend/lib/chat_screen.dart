import 'package:flutter/material.dart';

// ---------------------------------------------------------
// 1. ANA SOHBET EKRANI (Stateful Widget)
// ---------------------------------------------------------
class DiagnosticChatScreen extends StatefulWidget {
  const DiagnosticChatScreen({Key? key}) : super(key: key);

  @override
  State<DiagnosticChatScreen> createState() => _DiagnosticChatScreenState();
}

class _DiagnosticChatScreenState extends State<DiagnosticChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  
  // Örnek mesaj listesi (Arayüzü test etmek için)
  final List<Map<String, dynamic>> _messages = [
    {
      "text": "Merhaba! Ben Raylı Sistemler Bakım Asistanı. Sistem arızaları ve bakım süreçleri hakkında bana soru sorabilirsin.",
      "isUser": false,
      "sources": <Map<String, String>>[]
    }
  ];

  bool _isLoading = false;

  // Mesaj gönderme fonksiyonu (Simülasyon)
  void _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    // Kullanıcı mesajını ekle
    setState(() {
      _messages.add({
        "text": text,
        "isUser": true,
        "sources": <Map<String, String>>[]
      });
      _isLoading = true;
    });

    _messageController.clear();
    _scrollToBottom();

    // Yapay zeka cevabını taklit eden 2 saniyelik bekleme
    await Future.delayed(const Duration(seconds: 2));

    // Yapay zeka cevabını ve PDF referans kartlarını ekle
    setState(() {
      _isLoading = false;
      _messages.add({
        "text": "Kapı mekanizmasındaki kilitlenme arızası genelde sensör hizalamasındaki sapmadan kaynaklanır. Sinyal hatlarını ve limit switch ayarlarını kontrol etmeniz önerilir.",
        "isUser": false,
        "sources": [
          {"doc": "Rayli_Sistemler_Bakim_Klavuzu.pdf", "page": "14"},
          {"doc": "SMC_Kapi_Sistemleri_Diyagrami.pdf", "page": "3"}
        ]
      });
    });
    
    _scrollToBottom();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFAFAFAF), // Açık, ferah arka plan
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAlignment.start,
          children: [
            Text('Raylı Sistemler Asistanı', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text('RAG Destekli Teşhis Sistemi', style: TextStyle(fontSize: 12, color: Colors.white70)),
          ],
        ),
        backgroundColor: const Color(0xFF1E293B), // Koyu şık gri/mavi tonu
        foregroundColor: Colors.white,
        elevation: 2,
      ),
      body: Column(
        children: [
          // Mesaj Akış Alanı
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(vertical: 16.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                final isUser = message['isUser'] as bool;
                final sources = message['sources'] as List<dynamic>? ?? [];

                return Column(
                  crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
                  children: [
                    // Mesaj Balonu
                    ModernMessageBubble(
                      text: message['text'] as String,
                      isUser: isUser,
                    ),
                    
                    // PDF Referans Kartları (Yapay zeka mesajları için)
                    if (!isUser && sources.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(left: 8.0, bottom: 8.0),
                        child: Column(
                          children: sources.map((source) {
                            return ReferenceCard(
                              documentName: source['doc']!,
                              pageNumber: source['page']!,
                            );
                          }).toList(),
                        ),
                      ),
                  ],
                );
              },
            ),
          ),
          
          // Düşünüyor Animasyonu
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
              child: Align(
                alignment: Alignment.centerLeft,
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF1E293B)),
                ),
              ),
            ),

          // Alt Mesaj Yazma Alanı
          ModernInputField(
            controller: _messageController,
            onSend: _sendMessage,
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------
// 2. ÖZEL BİLEŞENLER (Bubles, Cards, Input)
// ---------------------------------------------------------

class ModernMessageBubble extends StatelessWidget {
  final String text;
  final bool isUser;

  const ModernMessageBubble({Key? key, required this.text, required this.isUser}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4.0, horizontal: 16.0),
        padding: const EdgeInsets.all(14.0),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF2563EB) : Colors.white, // Kullanıcıya mavi, Asistana beyaz
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isUser ? 16 : 2),
            bottomRight: Radius.circular(isUser ? 2 : 16),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 6,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Text(
          text,
          style: TextStyle(
            color: isUser ? Colors.white : const Color(0xFF1F2937),
            fontSize: 14.5,
            height: 1.4,
          ),
        ),
      ),
    );
  }
}

class ReferenceCard extends StatelessWidget {
  final String documentName;
  final String pageNumber;

  const ReferenceCard({Key? key, required this.documentName, required this.pageNumber}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 3.0, horizontal: 16.0),
      width: MediaQuery.of(context).size.width * 0.72,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFEFF6FF),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFBFDBFE), width: 1),
      ),
      child: Row(
        children: [
          const Icon(Icons.picture_as_pdf, color: Colors.redAccent, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAlignment.start,
              children: [
                Text(
                  documentName,
                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12, color: Color(0xFF1E3A8A)),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text("Sayfa: $pageNumber", style: const TextStyle(color: Color(0xFF6B7280), fontSize: 11)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class ModernInputField extends StatelessWidget {
  final TextEditingController controller;
  final VoidCallback onSend;

  const ModernInputField({Key? key, required this.controller, required this.onSend}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 10.0),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -3),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16.0),
                decoration: BoxDecoration(
                  color: const Color(0xFFF3F4F6),
                  borderRadius: BorderRadius.circular(24.0),
                ),
                child: TextField(
                  controller: controller,
                  onSubmitted: (_) => onSend(),
                  decoration: const InputDecoration(
                    hintText: "Arıza detayı veya soru yazın...",
                    hintStyle: TextStyle(color: Colors.black38, fontSize: 14),
                    border: InputBorder.none,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            InkWell(
              onTap: onSend,
              borderRadius: BorderRadius.circular(24),
              child: const CircleAvatar(
                radius: 22,
                backgroundColor: Color(0xFF2563EB),
                child: Icon(Icons.send_rounded, color: Colors.white, size: 20),
              ),
            ),
          ],
        ),
      ),
    );
  }
}