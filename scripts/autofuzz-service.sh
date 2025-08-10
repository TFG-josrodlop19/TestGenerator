!/bin/bash

PROJECT_DIR=""
PYTHON_EXEC=""
MAIN_SCRIPT=""

case "\$1" in
    start)
        echo "Starting Autofuzz..."
        
        # Start Vexgen
        cd "\${PROJECT_DIR}/vexgen"
        docker compose up -d --build

        # Wait for Vexgen to be ready
        echo "⏳ Waiting for Vexgen to be ready..."
        max_attempts=30
        attempt=0
        
        while [ \$attempt -lt \$max_attempts ]; do
            if curl -s http://localhost:8080/health >/dev/null 2>&1 || curl -s http://localhost:8080 >/dev/null 2>&1; then
                echo "Vexgen is ready"
                break
            fi
            sleep 2
            attempt=\$((attempt + 1))
        done
        
        if [ \$attempt -ge \$max_attempts ]; then
            echo "Timeout waiting for Vexgen, but continuing..."
        fi
        
        echo "Autofuzz is running"
        ;;
    stop)
        echo "Stopping Autofuzz..."

        # Stop Vexgen
        echo "Stopping Vexgen..."
        cd "\${PROJECT_DIR}/vexgen"
        docker compose down

        echo "Autofuzz stopped"
        ;;
    restart)
        echo "Restarting Autofuzz..."
        \$0 stop
        sleep 3
        \$0 start
        ;;
    *)
        echo "Uso: \$0 {start|stop|restart}"
        exit 1
        ;;
esac