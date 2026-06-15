package com.gopi.finextract;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;

import java.io.File;
import java.io.FileOutputStream;
import android.util.Base64;

@CapacitorPlugin(name = "PythonBridge")
public class PythonBridgePlugin extends Plugin {

    private PyObject logic;

    @Override
    public void load() {
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(getContext()));
        }
        Python py = Python.getInstance();
        logic = py.getModule("logic");
        logic.callAttr("init_app");
    }

    @PluginMethod
    public void listDocuments(PluginCall call) {
        try {
            String json = logic.callAttr("list_docs").toString();
            JSObject ret = new JSObject();
            ret.put("json", json);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject(e.getMessage());
        }
    }

    @PluginMethod
    public void uploadDocument(PluginCall call) {
        String name = call.getString("name");
        String base64Data = call.getString("data");
        try {
            byte[] data = Base64.decode(base64Data, Base64.DEFAULT);
            File file = new File(getContext().getFilesDir(), name);
            try (FileOutputStream fos = new FileOutputStream(file)) {
                fos.write(data);
            }
            int id = logic.callAttr("add_doc", name, file.getAbsolutePath()).toInt();
            JSObject ret = new JSObject();
            ret.put("id", id);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject(e.getMessage());
        }
    }

    @PluginMethod
    public void deleteDocument(PluginCall call) {
        int id = call.getInt("id");
        try {
            logic.callAttr("delete_doc", id);
            call.resolve();
        } catch (Exception e) {
            call.reject(e.getMessage());
        }
    }

    @PluginMethod
    public void runExtraction(PluginCall call) {
        int id = call.getInt("id");
        String kpis = call.getString("kpis");
        String custom = call.getString("custom");
        try {
            String json = logic.callAttr("run_extraction", id, kpis, custom).toString();
            JSObject ret = new JSObject();
            ret.put("json", json);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject(e.getMessage());
        }
    }

    @PluginMethod
    public void getResults(PluginCall call) {
        int id = call.getInt("id");
        try {
            String json = logic.callAttr("get_results", id).toString();
            JSObject ret = new JSObject();
            ret.put("json", json);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject(e.getMessage());
        }
    }

    @PluginMethod
    public void exportExcel(PluginCall call) {
        int id = call.getInt("id");
        try {
            String base64 = logic.callAttr("export_excel", id).toString();
            JSObject ret = new JSObject();
            ret.put("data", base64);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject(e.getMessage());
        }
    }
}
