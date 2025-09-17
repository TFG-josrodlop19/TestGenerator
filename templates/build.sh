#!/bin/bash -eu

# Step 1: Build the project with Maven
echo "Compilando proyecto con Maven..."
mvn -q clean dependency:copy-dependencies -DoutputDirectory=target/dependency-jars

# Step 2: Set up the classpath
echo "Configurando classpath..."
BUILD_CLASSPATH="$JAZZER_API_PATH:$(find "target/dependency-jars" -name "*.jar" | paste -sd: -)"

# Step 3: Compile main classes
echo "Compilando clases principales..."
javac -encoding UTF-8 -cp "$BUILD_CLASSPATH" $(find src/main/java/ -name "*.java") -d $OUT

# Step 4: Compile fuzzers
echo "Compilando fuzzers..."

# Find and compile each fuzzer
find src/test/java/ -name "*Fuzzer.java" | while read -r fuzzer_file; do
    fuzzer_name=$(basename "$fuzzer_file" .java)
    echo "Procesando: $fuzzer_name"
    
    # Compliling the fuzzer
    if javac -encoding UTF-8 -cp "$BUILD_CLASSPATH:$OUT" "$fuzzer_file" -d $OUT 2>/dev/null; then
        echo "✅ $fuzzer_name: COMPILED SUCCESSFULLY"
    else
        echo "❌ $fuzzer_name: FAILED TO COMPILE"
    fi
done

# Step 5: Copy artifacts
cp target/dependency-jars/*.jar $OUT/
cp /usr/local/bin/jazzer_driver $OUT/
cp /usr/local/bin/jazzer_agent_deploy.jar $OUT/

# Step 6: Create dynamic launchers
find "$OUT" -name "*Fuzzer.class" | while read -r fuzzer_class_file; do
    fuzzer_class_name=$(echo "$fuzzer_class_file" | sed "s|^$OUT/||; s|\.class$||; s|/|\.|g")
    fuzzer_script_name=$(basename "$fuzzer_class_file" .class)

    echo "Creating launcher for: $fuzzer_class_name"

    cat > "$OUT/$fuzzer_script_name" << EOF
#!/bin/bash
set -eu
this_dir=\$(dirname "\$0")
cd "\$this_dir"
JARS=\$(find . -name "*.jar" | paste -sd:)
RUNTIME_CLASSPATH=".:\$JARS"
LD_LIBRARY_PATH="\${JVM_LD_LIBRARY_PATH:-.}" \\
./jazzer_driver \\
  --agent_path=./jazzer_agent_deploy.jar \\
  --cp="\$RUNTIME_CLASSPATH" \\
  --target_class=$fuzzer_class_name \\
  --jvm_args="-Djava.awt.headless=true" \\
  "\$@"
EOF

    chmod +x "$OUT/$fuzzer_script_name"
done

echo "Build completado."