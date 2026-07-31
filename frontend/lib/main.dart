import 'package:flutter/material.dart';

import 'chat_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    const Color surface = Color(0xFF09111F);
    const Color surfaceAlt = Color(0xFF0F1B2D);
    const Color accent = Color(0xFF4DA2FF);

    return MaterialApp(
      title: 'Arıza Teşhis Asistanı',
      theme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
        scaffoldBackgroundColor: surface,
        colorScheme: const ColorScheme.dark(
          primary: accent,
          secondary: Color(0xFF7DD3FC),
          surface: surface,
          surfaceContainerHighest: surfaceAlt,
          error: Color(0xFFFF7A7A),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.transparent,
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: surfaceAlt,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(22),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(22),
            borderSide: const BorderSide(color: Color(0xFF243247)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(22),
            borderSide: const BorderSide(color: accent),
          ),
        ),
      ),
      debugShowCheckedModeBanner: false,
      home: const DiagnosticChatScreen(),
    );
  }
}
