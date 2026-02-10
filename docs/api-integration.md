# CloudPrintd API Integration Guide

## Salesforce Integration

### Overview
This guide covers integrating CloudPrintd with Salesforce to enable cloud-to-printer communication.

## Setup Named Credential

### Step 1: Create Named Credential

1. In Salesforce Setup, navigate to: **Security → Named Credentials**
2. Click **New Named Credential**
3. Configure:
   - **Label:** CloudPrintd Server
   - **Name:** CloudPrintd_Server
   - **URL:** Your CloudPrintd server URL (e.g., `https://yourserver.com` or `http://192.168.1.100:8000`)
   - **Identity Type:** Named Principal
   - **Authentication Protocol:** Password Authentication
   - **Username:** `api` (any value works)
   - **Password:** Your CloudPrintd API token
   - **Generate Authorization Header:** Checked
   - **Allowed Protocols:** HTTPS (or HTTP for local testing)

### Step 2: Configure Remote Site (if needed)

If not using Named Credential with callouts:

1. Setup → Security → Remote Site Settings
2. Add your CloudPrintd URL

## API Endpoints

### Base URL
```
http://your-CloudPrintd-server:8000/api/v1
```

### Authentication
All API requests require Bearer token authentication:
```
Authorization: Bearer YOUR_API_TOKEN
```

### Print Job Submission

**Endpoint:** `POST /print`

**Request Body:**
```json
{
  "printer": "warehouse_zebra",
  "content": "^XA^FO50,50^A0N,50,50^FDHello World^FS^XZ",
  "format": "zpl",
  "copies": 1,
  "job_name": "Order_12345"
}
```

**Parameters:**
- `printer` (string, required): Printer identifier
- `content` (string, required): Print content (ZPL, PDF base64, or raw text)
- `format` (string, optional): Content format - "zpl", "pdf", "raw", or "text" (default: "zpl")
- `copies` (integer, optional): Number of copies (1-100, default: 1)
- `job_name` (string, optional): Job identifier

**Response:**
```json
{
  "job_id": "job_1234567890_abc123",
  "status": "completed",
  "message": "Successfully sent 1 copy to printer",
  "printer": "warehouse_zebra"
}
```

### List Printers

**Endpoint:** `GET /printers`

**Response:**
```json
[
  {
    "id": "warehouse_zebra",
    "config": {
      "type": "zebra_raw",
      "display_name": "Warehouse Zebra ZT411",
      "ip": "192.168.1.100",
      "port": 9100,
      "location": "Warehouse Bay 3"
    },
    "status": "online",
    "last_check": "2026-02-10T15:30:00Z"
  }
]
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 86400.5,
  "printers_configured": 3,
  "printers_online": 2
}
```

## Apex Examples

### Example 1: Simple Print Job

```apex
public class CloudPrintdService {
    
    public static void printLabel(String printerName, String zplContent) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:CloudPrintd_Server/api/v1/print');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        
        Map<String, Object> requestBody = new Map<String, Object>{
            'printer' => printerName,
            'content' => zplContent,
            'format' => 'zpl',
            'copies' => 1
        };
        
        req.setBody(JSON.serialize(requestBody));
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        if (res.getStatusCode() == 200) {
            Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            System.debug('Print job submitted: ' + result.get('job_id'));
        } else {
            throw new CalloutException('Print failed: ' + res.getBody());
        }
    }
}
```

### Example 2: Print Shipping Label from Order

```apex
public class ShippingLabelPrinter {
    
    @future(callout=true)
    public static void printShippingLabel(Id orderId) {
        // Get order details
        Order order = [SELECT Id, OrderNumber, ShippingStreet, ShippingCity, 
                              ShippingPostalCode, Account.Name 
                       FROM Order WHERE Id = :orderId];
        
        // Generate ZPL label
        String zpl = generateShippingLabelZPL(order);
        
        // Send to printer
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:CloudPrintd_Server/api/v1/print');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        
        Map<String, Object> requestBody = new Map<String, Object>{
            'printer' => 'shipping_zebra',
            'content' => zpl,
            'format' => 'zpl',
            'copies' => 2,
            'job_name' => 'Order_' + order.OrderNumber
        };
        
        req.setBody(JSON.serialize(requestBody));
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        if (res.getStatusCode() != 200) {
            System.debug(LoggingLevel.ERROR, 'Print failed: ' + res.getBody());
        }
    }
    
    private static String generateShippingLabelZPL(Order order) {
        return '^XA' +
               '^FO50,50^A0N,40,40^FDOrder: ' + order.OrderNumber + '^FS' +
               '^FO50,100^A0N,30,30^FD' + order.Account.Name + '^FS' +
               '^FO50,140^A0N,25,25^FD' + order.ShippingStreet + '^FS' +
               '^FO50,170^A0N,25,25^FD' + order.ShippingCity + ', ' + order.ShippingPostalCode + '^FS' +
               '^XZ';
    }
}
```

### Example 3: Batch Printing with Error Handling

```apex
public class BatchLabelPrinter implements Database.Batchable<SObject>, Database.AllowsCallouts {
    
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id, Name, ProductCode, Barcode__c 
            FROM Product2 
            WHERE NeedsPrint__c = true
        ]);
    }
    
    public void execute(Database.BatchableContext bc, List<Product2> products) {
        for (Product2 product : products) {
            try {
                printProductLabel(product);
                product.NeedsPrint__c = false;
                product.LastPrinted__c = DateTime.now();
            } catch (Exception e) {
                System.debug(LoggingLevel.ERROR, 'Failed to print ' + product.Name + ': ' + e.getMessage());
                // Could log to custom object for retry
            }
        }
        
        update products;
    }
    
    public void finish(Database.BatchableContext bc) {
        System.debug('Batch printing complete');
    }
    
    private void printProductLabel(Product2 product) {
        String zpl = '^XA' +
                    '^FO50,50^A0N,30,30^FD' + product.Name + '^FS' +
                    '^FO50,100^BY2^BCN,70,Y,N,N^FD' + product.Barcode__c + '^FS' +
                    '^XZ';
        
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:CloudPrintd_Server/api/v1/print');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setTimeout(30000);
        
        Map<String, Object> requestBody = new Map<String, Object>{
            'printer' => 'warehouse_zebra',
            'content' => zpl,
            'format' => 'zpl',
            'job_name' => 'Product_' + product.ProductCode
        };
        
        req.setBody(JSON.serialize(requestBody));
        
        Http http = new Http();
        HttpResponse res = http.send(req);
        
        if (res.getStatusCode() != 200) {
            throw new CalloutException('Print failed: ' + res.getBody());
        }
    }
}
```

### Example 4: Lightning Web Component Integration

**printLabel.js:**
```javascript
import { LightningElement, api } from 'lwc';
import printLabel from '@salesforce/apex/CloudPrintdService.printLabel';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class PrintLabel extends LightningElement {
    @api recordId;
    
    handlePrint() {
        printLabel({ 
            recordId: this.recordId,
            printerName: 'warehouse_zebra'
        })
        .then(() => {
            this.showToast('Success', 'Label sent to printer', 'success');
        })
        .catch(error => {
            this.showToast('Error', error.body.message, 'error');
        });
    }
    
    showToast(title, message, variant) {
        this.dispatchEvent(
            new ShowToastEvent({ title, message, variant })
        );
    }
}
```

## Error Handling

### Common Error Codes

| Status Code | Meaning | Action |
|------------|---------|---------|
| 400 | Bad Request | Check request parameters |
| 401 | Unauthorized | Verify API token |
| 403 | Forbidden | Check IP whitelist |
| 404 | Not Found | Verify printer exists |
| 500 | Server Error | Check CloudPrintd logs |

### Error Response Format

```json
{
  "error": true,
  "status_code": 404,
  "message": "Printer 'invalid_printer' not found"
}
```

## Best Practices

1. **Use Future Methods:** Always use `@future(callout=true)` for async printing
2. **Error Handling:** Implement try-catch and log failures
3. **Timeout:** Set appropriate timeout values (30-60 seconds)
4. **Retry Logic:** Implement retry for transient failures
5. **Monitoring:** Track print success/failure rates
6. **Testing:** Mock HTTP callouts in test classes

## Testing in Salesforce

```apex
@isTest
private class CloudPrintdServiceTest {
    
    @isTest
    static void testPrintLabel() {
        Test.setMock(HttpCalloutMock.class, new CloudPrintdMock());
        
        Test.startTest();
        CloudPrintdService.printLabel('test_printer', '^XA^FDTest^FS^XZ');
        Test.stopTest();
        
        // Add assertions
    }
    
    private class CloudPrintdMock implements HttpCalloutMock {
        public HttpResponse respond(HttpRequest req) {
            HttpResponse res = new HttpResponse();
            res.setStatusCode(200);
            res.setBody('{"job_id":"test123","status":"completed"}');
            return res;
        }
    }
}
```

## Rate Limits

CloudPrintd doesn't impose strict rate limits, but consider:
- Raspberry Pi hardware limitations
- Network bandwidth
- Printer processing speed

Recommended: < 100 print jobs per minute

## Support

For integration issues:
1. Check [Troubleshooting Guide](troubleshooting.md)
2. Review CloudPrintd logs: `/home/CloudPrintd/logs/CloudPrintd.log`
3. Test API using curl before debugging Salesforce code
4. Verify printer status via dashboard
